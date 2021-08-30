"""
Brick ops module deals with the functions related to brick related operations.
"""
# pylint: disable=too-many-lines

from time import sleep
import random
from common.ops.abstract_ops import AbstractOps


class BrickOps(AbstractOps):
    """
    Class which is responsible for methods for brick related operations.
    """

    def add_brick(self, volname: str, brick_str: str, node: str,
                  force: bool = False, excep: bool = True,
                  **kwargs) -> dict:
        """
        # TODO: Function has to designed for dispersed, distributed-dispersed,
                arbiter and distributed-arbiter.
        This function adds bricks to the volume volname.

        Args:

            volname (str): The volume in which the brick has to be added.
            brick_str (str): string of brick command.
            node (str): The node on which the command is to be run.
            force (bool): If set to True will add force in the command
                          being executed.
            replica_count (int): Updated replica count
            arbiter_count (int): Updated arbiter count
            excep (bool): exception flag to bypass the exception if the
                          add brick command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True
        Kwargs:
            **kwargs
                The keys, values in kwargs are:
                    - replica_count : (int)|None.
                        Updated replica count
                    - arbiter_count : (int)|None
                        Updated arbiter count
        Returns:
            ret: A dictionary consisting
                    - Flag : Flag to check if connection failed
                    - msg : message
                    - error_msg: error message
                    - error_code: error code returned
                    - cmd : command that got executed
                    - node : node on which the command got executed
        """
        replica = arbiter = ''
        if 'replica_count' in kwargs:
            replica = (f"replica {kwargs['replica_count']}")
            if 'arbiter_count' in kwargs:
                arbiter = (f"arbiter {kwargs['arbiter_count']}")

        cmd = (f"gluster vol add-brick {volname} {replica} {arbiter}"
               f" {brick_str} --mode=script --xml")

        if force:
            cmd = (f"{cmd} force")
        ret = self.execute_abstract_op_node(cmd, node, excep)

        if not excep and ret['msg']['opRet'] != '0':
            return ret

        server_brick = {}
        for brickd in brick_str.split(' '):
            node, bpath = brickd.split(':')
            if node not in server_brick:
                server_brick[node] = []
            server_brick[node].append(bpath)
        self.es.add_bricks_to_brickdata(volname, server_brick)

        return ret

    def remove_brick(self, node: str, volname: str, brick_list: list,
                     option: str, replica_count: int = None,
                     excep: bool = True) -> dict:
        """
        This function removes the given list of bricks from the volume.

        Args:

            node (str): Node on which the command has to be executed.
            volname (str): The volume from which brick(s) have to be removed.
            brick_list (list): The list of bricks to be removed
            option (str): Remove brick options:
                          <start|stop|status|commit|force>
            replica_count (int): Optional parameter with default value as None.
            excep (bool): exception flag to bypass the exception if the
                          remove brick command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True
        Returns:
            ret: A dictionary consisting
                    - Flag : Flag to check if connection failed
                    - msg : message
                    - error_msg: error message
                    - error_code: error code returned
                    - cmd : command that got executed
                    - node : node on which the command got executed
        NOTE: For now the option change is to be handled by the user. The count
        values have to be modified after remove brick is a success. Also,
        a TODO is to check the commit force option and its incorporation in
        this function.
        """
        if not isinstance(brick_list, list):
            brick_list = [brick_list]

        replica = ''
        if replica_count is not None:
            replica = (f"replica {replica_count}")

        brick_cmd = " ".join(brick_list)
        cmd = (f"gluster vol remove-brick {volname} {replica} {brick_cmd}"
               f" {option} --mode=script --xml")

        ret = self.execute_abstract_op_node(cmd, node, excep)

        if not excep and ret['msg']['opRet'] != '0':
            return ret

        if option in ['commit', 'force']:
            server_brick = {}
            for brickd in brick_list:
                node, bpath = brickd.split(':')
                if node not in server_brick:
                    server_brick[node] = []
                server_brick[node].append(bpath)
            self.es.remove_bricks_from_brickdata(volname, server_brick)

        return ret

    def replace_brick(self, node: str, volname: str,
                      src_brick: str, dest_brick: str,
                      excep: bool = True) -> dict:
        """
        This function replaces one brick(source brick)
        with the another brick(destination brick) on the volume.

        Args:
            node (str): The node on which the command has to be executed
            volname (str): The volume on which the bricks have to be replaced.
            src_brick (str) : The source brick name
            dest_brick (str) : The destination brick name
            excep (bool): exception flag to bypass the exception if the
                          replace brick command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True

        Returns:
            ret: A dictionary consisting
                    - Flag : Flag to check if connection failed
                    - msg : message
                    - error_msg: error message
                    - error_code: error code returned
                    - cmd : command that got executed
                    - node : node on which the command got executed
        """
        # TODO:server val to modify the new brick path
        cmd = (f"gluster volume replace-brick "
               f"{volname} {src_brick} {dest_brick} "
               f"commit force --xml")

        ret = self.execute_abstract_op_node(cmd, node, excep)
        if not excep and ret['msg']['opRet'] != '0':
            return ret

        self.es.replace_brick_from_brickdata(volname, src_brick,
                                             dest_brick)

        return ret

    def replace_brick_from_volume(self, volname: str, node: str,
                                  servers: list, src_brick: str = None,
                                  dst_brick: str = None,
                                  delete_brick: bool = True,
                                  brick_roots: list = None) -> bool:
        """
        Replace faulty brick from a volume

        Args:
            volname (str): Volume in which the brick has to be replaced
            node (str): Node on which command has to be executed
            server_list (list): List of servers in the cluster

        Optional:
            src_brick (str): Brick to be replaced
            dst_brick (str): New brick which will replace the old one
            delete_brick (bool): True, if the old brick should be deleted
                                 otherwise False. (Default is True)

        Returns:
            bool: True if the replace brick operation was successful,
                  False if the operation failed.
        """
        if not isinstance(servers, list):
            servers = [servers]

        # Check if volume exists
        if not self.es.does_volume_exists(volname):
            self.logger.error(f"Volume {volname} does not exist")
            return False

        # Get subvols
        subvols_list = self.get_subvols(volname, node)

        if not src_brick:
            # Randomly select a brick to replace
            src_brick = (random.choice(random.choice(subvols_list)))

        if not dst_brick:
            _, dst_brick = self.form_brick_cmd(servers, brick_roots,
                                               volname, 1, True)

            if not dst_brick:
                self.logger.error("Failed to get a new brick to replace")

        # Bring src brick offline
        if not self.bring_bricks_offline(volname, src_brick):
            self.logger.error("Failed to bring source brick offline")

        # Wait for src brick to go offline
        if not self.wait_for_bricks_to_go_offline(volname, src_brick):
            self.logger.error("Brick is still not offline for replace brick"
                              " operation")
            return False

        # Check volume status before replace brick operation
        ret = self.get_volume_status(volname, node)
        if ret is None:
            self.logger.error("Failed to get volume status")
            return False

        # Perform replace brick
        ret = self.replace_brick(node, volname, src_brick, dst_brick, False)
        if ret['msg']['opRet'] != '0':
            self.logger.error(f"Failed to replace brick: {src_brick}")
            return False

        # Delete old brick
        if delete_brick:
            ret = self.delete_bricks(src_brick)
            if not ret:
                return False

        return True

    def reset_brick(self, node: str, volname: str, src_brick: str,
                    option: str, dst_brick=None, force=False):
        """
        Resets brick in a volume

        Args:
            node (str) : Node on which the command has to be executed
            volname (str) : Name of the volume on which the brick
                            has to be reset
            src_brick (str) : Name of the source brick
            dst_brick (str) : Name of the destination brick
            option (str) : Options for reset brick : start | commit | force

        Kwargs:
            force (bool) : If this option is set to True,
                           then reset brick will get executed
                           with force option

        Returns:
            ret: A dictionary consisting
                    - Flag : Flag to check if connection failed
                    - msg : message
                    - error_msg: error message
                    - error_code: error code returned
                    - cmd : command that got executed
                    - node : node on which the command got executed
        """

        if option == "start":
            cmd = f"gluster vol reset-brick {volname} {src_brick} start"

        elif option == "commit":
            if dst_brick is None:
                dst_brick = src_brick

            cmd = (f"gluster vol reset-brick {volname} {src_brick} {dst_brick}"
                   f" {option}")

            if force:
                cmd = f"{cmd} force"

        ret = self.execute_abstract_op_node(cmd=cmd, node=node)

        return ret

    @staticmethod
    def _get_brick_cmd(brick, volname, iteration, server_val, brick_cmd,
                       brick_dict):
        """
        Form the brick command and the brick dict using the server and
        the brick
        """
        brick_path_val = f"{brick}/{volname}-{iteration}"
        if server_val not in brick_dict.keys():
            brick_dict[server_val] = []
        brick_dict[server_val].append(brick_path_val)
        brick_cmd = (f"{brick_cmd} {server_val}:{brick_path_val}")
        return brick_dict, brick_cmd

    @staticmethod
    def _get_index(server_list, brick_cmd):
        """
        Get the index of the server in the server list
        """
        ind = 0
        index = 0
        server_val = brick_cmd.split(" ")[-1].split(":")[0]
        try:
            ind = server_list.index(server_val)
        except ValueError:
            ind = -1

        if ind != -1 and ind == 0 and len(server_list) > 1:
            index = 1

        return index

    def form_brick_cmd(self, server_list: list, brick_root: dict,
                       volname: str, mul_fac: int,
                       add_flag: bool = False) -> tuple:
        """
        # TODO: Function has to designed for dispersed, distributed-dispersed,
                arbiter and distributed-arbiter.
        This function helps in forming
        the brick command

        Args:
            server_list (list): List of servers
            brick_root (dict) : List of brick roots
            volname (str) : Name of the volume
            mul_fac (int) : Stores the number of bricks
                            needed to form the brick command
            add_flag (bool): Indicates whether the command creation is for
                             add/replace brick scenario or volume creation.
                             Optional parameter which by default is False.

        Returns:

        A tuple containing:
            brick_dict (dict) : Dictionary of servers and their
                                corresponding brick roots
            brick_cmd (str) : Command which contains the brick
                              paths.
        """
        if not isinstance(server_list, list):
            server_list = [server_list]

        brick_dict = {}
        brick_cmd = ""
        server_val = ""
        brick_iter = 0
        used_bricks, unused_bricks = {}, {}
        used_servers, unused_servers = [], []
        last_node = ""
        iteration = 0
        index = 0
        iter_add = 0

        if add_flag:
            brick = ""
            brick_list = self.get_all_bricks(volname, server_list[0])
            for brick in brick_list:
                brick_num = int(brick.split('-')[-1])
                if iter_add < brick_num:
                    iter_add = brick_num

                node, brick_path = brick.split(':')

                # Create used bricks list
                root_brick = brick_path[0:brick_path.rfind('/')]
                if node not in used_bricks.keys():
                    used_bricks[node] = []
                used_bricks[node].append(root_brick)

                # Create used servers list
                used_servers.append(node)

            # Save the last used node, so that new brick addition starts from
            # a different node
            last_node = brick.split(':')[0]
            iter_add = iter_add + 1

        # Create unused servers list
        if used_servers:
            for server in server_list:
                if server not in used_servers:
                    unused_servers.append(server)

        # Create the unused bricks dict
        if used_bricks:
            for node, brick in brick_root.items():
                if node in server_list:
                    if node not in used_bricks.keys():
                        unused_bricks[node] = brick_root[node].copy()
                    else:
                        for br in brick:
                            if br not in used_bricks[node]:
                                if node not in unused_bricks.keys():
                                    unused_bricks[node] = []
                                unused_bricks[node].append(br)

        # If we have unused servers, use them
        while(len(unused_servers) > 0 and iteration < mul_fac):
            server_val = unused_servers[0]
            brick = unused_bricks[server_val][0]
            brick_dict, brick_cmd = self._get_brick_cmd(brick, volname,
                                                        iteration + iter_add,
                                                        server_val, brick_cmd,
                                                        brick_dict)
            # Remove the server from the unused servers list and
            # unused bricks dict as well
            unused_servers.remove(server_val)
            unused_bricks[server_val].remove(brick)
            iteration += 1

        # If we have unused bricks in some node, use them
        if unused_bricks.keys():
            nodes = list(unused_bricks.keys())
            # Use a different node than the last used node, if we have
            # extra nodes
            if brick_cmd:
                index = self._get_index(nodes, brick_cmd)
                if index == 1:
                    server_val = nodes[1]
                    index = -1
                else:
                    server_val = nodes[0]
                    index = 0
            else:
                if last_node == nodes[0] and len(nodes) > 1:
                    server_val = nodes[1]
                    index = -1
                else:
                    server_val = nodes[0]
                    index = 0

            while(unused_bricks.keys() and iteration < mul_fac):
                brick = unused_bricks[server_val][0]
                brick_dict, brick_cmd = (self._get_brick_cmd(brick, volname,
                                         iteration + iter_add, server_val,
                                         brick_cmd, brick_dict))
                unused_bricks[server_val].remove(brick)
                if not unused_bricks[server_val]:
                    unused_bricks.pop(server_val)
                    nodes.remove(server_val)

                index += 1
                iteration += 1
                if len(nodes) > 0 and index >= len(nodes):
                    server_val = nodes[0]
                    index = 0
                elif len(nodes) > 0:
                    server_val = nodes[index]
                else:
                    break

        # Create bricks serially from the total bricks available in the
        # brick_root
        index = 0
        if brick_cmd:
            index = self._get_index(nodes, brick_cmd)
        elif last_node == server_list[index]:
            index += 1

        while iteration < mul_fac:
            # If no more servers left in brick_root dict, start from beginning
            # And, update the brick_iter value to check for multiple bricks
            # within a node
            if index == len(server_list):
                index = 0
                brick_iter += 1

            i = 0
            while i < len(server_list):
                if len(brick_root[server_list[index]]) - 1 >= brick_iter:
                    break
                index += 1
                if index == len(server_list):
                    index = 0
                i += 1

            # If all the bricks in the brick_root is exhausted sttart from
            # the beginning
            if i == len(server_list):
                index = 0
                brick_iter = 0

            server_val = server_list[index]
            brick = brick_root[server_val][brick_iter]
            brick_dict, brick_cmd = (self._get_brick_cmd(brick, volname,
                                     iteration + iter_add, server_list[index],
                                     brick_cmd, brick_dict))
            index += 1
            iteration += 1

        brick_cmd = brick_cmd.lstrip(" ")

        return (brick_dict, brick_cmd)

    def form_brick_cmd_to_add_brick(self, node: str, volname: str,
                                    server_list: list, brick_root: dict,
                                    **kwargs) -> str:
        """
        Forms list of bricks to add-bricks to the volume

        Args:
            volname (str): volume name
            server_list (list): List of servers in the storage pool.
            brick_root (dict): Dict containing list of brick roots for
                               each node
        Kwargs:
            The key, value in kwargs are:
            - replica_count (int): Increase the current_replica_count by
                                   replica_count
            - ditribute_count (int): Increase the current_distribute_count
                                     by distribute_count

        Returns:
            str: The brick cmd used to add-brick or,
            None: In case of failure
        """

        # Check if volume exists
        if not self.es.does_volume_exists(volname):
            self.logger.error(f"Volume {volname} doesn't exists.")
            return None

        # Check if the volume has to be expanded by n distribute count.
        distribute_count = None
        if 'distribute_count' in kwargs:
            distribute_count = int(kwargs['distribute_count'])

        # Check whether we need to increase the replica count of the volume
        replica_count = None
        if 'replica_count' in kwargs:
            replica_count = int(kwargs['replica_count'])

        if replica_count is None and distribute_count is None:
            distribute_count = 1

        # Check if the volume has to be expanded by n distribute count.
        num_of_distribute_bricks_to_add = 0
        if distribute_count:
            # Get Number of bricks per subvolume.
            bricks_per_subvol = self.get_num_of_bricks_per_subvol(node,
                                                                  volname)

            # Get number of bricks to add.
            if bricks_per_subvol is None:
                self.logger.error("Number of bricks per subvol is None. "
                                  "Something majorly went wrong on the volume"
                                  f" {volname}")
                return None

            num_of_distribute_bricks_to_add = (bricks_per_subvol
                                               * distribute_count)

        # Check if the volume has to be expanded by n replica count.
        num_of_replica_bricks_to_add = 0
        if replica_count:
            # Get Subvols
            subvols_info = self.get_subvols(volname, node)
            num_of_subvols = len(subvols_info)

            if num_of_subvols == 0:
                self.logger.error("No Sub-Volumes available for the volume "
                                  f"{volname}. Hence cannot proceed with "
                                  " add-brick")
                return None

            num_of_replica_bricks_to_add = replica_count * num_of_subvols

        # Calculate total number of bricks to add
        if (num_of_distribute_bricks_to_add != 0
                and num_of_replica_bricks_to_add != 0):
            num_of_bricks_to_add = (num_of_distribute_bricks_to_add
                                    + num_of_replica_bricks_to_add
                                    + (distribute_count * replica_count))
        else:
            num_of_bricks_to_add = (
                num_of_distribute_bricks_to_add
                + num_of_replica_bricks_to_add
            )

        # Form bricks list to add bricks to the volume.
        _, bricks_cmd = self.form_brick_cmd(server_list, brick_root, volname,
                                            num_of_bricks_to_add, True)
        return bricks_cmd

    def form_bricks_list_to_remove_brick(self, node: str, volname: str,
                                         subvol_num: list = None,
                                         replica_num: int = None,
                                         **kwargs) -> list:
        """
        Form bricks list for removing the bricks.

        Args:
            node (str): Node on which commands has to be executed
            volname (str): volume name

        Optional:
            subvol_num (int|list): int|List of sub volumes number to remove.
                For example: If subvol_num = [2, 5], Then we will be removing
                bricks from 2nd and 5th sub-volume of the given volume.
                The sub-volume number starts from 0.

            replica_num (int): Specify which replica brick to remove.
                If replica_num = 0, then 1st brick from each subvolume is
                removed. the replica_num starts from 0.

        Kwargs:
            **kwargs: The keys, values in kwargs are:
                    - replica_count : (int)|None. Specify the number of
                        replicas reduce
                    - distribute_count: (int)|None. Specify the distribute
                        count to reduce.

        Returns:
            list: List of bricks to remove from the volume.
            NoneType: None if volume doesn't exists or any other failure.
        """
        # pylint: disable=too-many-return-statements
        # Check if volume exists
        if not self.es.does_volume_exists(volname):
            self.logger.error(f"Volume {volname} doesn't exists.")
            return None

        # If distribute_count, replica_count or replica_leg , subvol_num is
        # not specified, then default shrink_volume to randomly pick
        # a subvolume to remove
        if ('distribute_count' not in kwargs
            and 'replica_count' not in kwargs
            and replica_num is None
                and subvol_num is None):
            kwargs['distribute_count'] = 1

        # Get Subvols
        subvols_list = self.get_subvols(volname, node)
        if not subvols_list:
            self.logger.error("No Sub-Volumes available for the volume "
                              f"{volname}")
            return None

        # Initialize bricks to remove
        bricks_list_to_remove = []

        # remove bricks by reducing replica count of the volume
        if replica_num is not None or 'replica_count' in kwargs:
            # Get replica count info.
            current_replica_count = self.get_replica_count(node, volname)

            # Get volume type info
            vol_type_info = self.get_volume_type_info(node, volname)
            if vol_type_info is None:
                self.logger.error("Unable to get the replica count info for "
                                  f"the volume {volname}")
                return None

            # Set is_arbiter to False
            is_arbiter = False

            # Calculate bricks to remove
            arbiter_count = int(vol_type_info['volume_type_info']
                                ['arbiterCount'])
            if arbiter_count == 1:
                is_arbiter = True

            # If replica_num is specified select the bricks of that replica
            # number from all the subvolumes.
            if replica_num is not None:
                if isinstance(replica_num, int):
                    replica_num = [replica_num]

                for each_replica_num in replica_num:
                    try:
                        bricks_list_to_remove.extend(
                            [subvol[each_replica_num]
                             for subvol in subvols_list])
                    except IndexError:
                        self.logger.error("Provided replica number "
                                          f"{replica_num} is greater than or"
                                          " equal to the existing replica "
                                          f"count {current_replica_count} of"
                                          f" the volume {volname}. Hence "
                                          "cannot proceed with forming bricks"
                                          " for remove-brick")
                        return None

            # If arbiter_volume, always remove the 3rd brick (arbiter brick)
            elif is_arbiter:
                bricks_list_to_remove.extend([subvol[-1]
                                              for subvol in subvols_list])

            # If replica_num is not specified nor it is arbiter volume,
            # randomly select the bricks to remove.
            else:
                replica_count = int(kwargs['replica_count'])

                if replica_count >= current_replica_count:
                    self.logger.error(f"Provided replica number {replica_num}"
                                      " is greater than or equal to the "
                                      "existing replica count "
                                      f"{current_replica_count} of the volume"
                                      f" {volname}. Hence cannot proceed with"
                                      " forming bricks for remove-brick")
                    return None

                sample = ([random.sample(subvol, replica_count)
                           for subvol in subvols_list])
                for item in sample:
                    bricks_list_to_remove.extend(item)

        # remove bricks from sub-volumes
        if subvol_num is not None or 'distribute_count' in kwargs:
            # select bricks of subvol_num specified
            if subvol_num is not None:
                if isinstance(subvol_num, int):
                    subvol_num = [subvol_num]
                for each_subvol_num in subvol_num:
                    try:
                        bricks_list_to_remove.extend(
                            subvols_list[each_subvol_num])

                    except IndexError:
                        self.logger.error("Invalid sub volume number: "
                                          f"{subvol_num} specified for "
                                          "removing the subvolume from the "
                                          f"volume: {volname}")
                        return None

            # select bricks from multiple subvols with number of
            # subvolumes specified as distribute_count argument.
            elif 'distribute_count' in kwargs:
                distribute_count = int(kwargs['distribute_count'])
                sample = random.sample(subvols_list, distribute_count)
                for item in sample:
                    bricks_list_to_remove.extend(item)

            # randomly choose a subvolume to remove-bricks from.
            else:
                bricks_list_to_remove.extend(random.choice(subvols_list))

        return list(set(bricks_list_to_remove))

    def are_bricks_offline(self, volname: str,
                           bricks_list: list, node: str,
                           strict: bool = True) -> bool:
        """
        This function checks if the given list of
        bricks are offline.

        Args:
            volname (str) : Volume name
            bricks_list (list) : list of bricks to check
            node (str) : the node on which comparison has to be done
            strict (bool) : To check strictly if all bricks are offline
        Returns:
            boolean value: True, if bricks are offline
                           False, if online
        """
        if not isinstance(bricks_list, list):
            bricks_list = [bricks_list]

        vol_status = self.get_volume_status(volname, node)

        vol_status_brick_list = []
        for n in vol_status[volname]['node']:
            if int(n['status']) == 1:
                brick = f"{n['hostname']}:{n['path']}"
                vol_status_brick_list.append(brick)

        online_brick_list = []
        ret = True

        for brick in bricks_list:
            if strict and brick in vol_status_brick_list:
                online_brick_list.append(brick)
                self.logger.error(f"Brick: {brick} is not offline")
                ret = False
            elif brick in vol_status_brick_list:
                self.logger.error(f"Brick: {brick} is not offline")
                return False

        if not ret:
            self.logger.error(f"Some of the bricks are not "
                              f"offline: {online_brick_list}")
            return ret

        self.logger.info(f"All bricks are offline: {bricks_list}")
        return ret

    def are_bricks_online(self, volname: str,
                          bricks_list: list, node: str,
                          strict: bool = True) -> bool:
        """
        This function checks if the given list of
        bricks are online.

        Args:
            volname (str) : Volume name
            bricks_list (list) : list of bricks to check
            node (str) : the node on which comparison has to be done
            strict (bool) : To check strictly if all bricks are online
        Returns:
            boolean value: True, if bricks are online
                           False, if offline
        """
        if not isinstance(bricks_list, list):
            bricks_list = [bricks_list]

        vol_status = self.get_volume_status(volname, node)

        vol_status_brick_list = []
        for brick in vol_status[volname]['node']:
            if int(brick['status']) == 1:
                brick_path = f"{brick['hostname']}:{brick['path']}"
                vol_status_brick_list.append(brick_path)

        offline_brick_list = []
        ret = True

        for brick in bricks_list:
            if strict and brick not in vol_status_brick_list:
                offline_brick_list.append(brick)
                self.logger.error(f"Brick: {brick} is not online")
                ret = False
            elif brick not in vol_status_brick_list:
                self.logger.error(f"Brick: {brick} is not online")
                return False

        if not ret:
            self.logger.error(f"Some of the bricks are "
                              f"not online: {offline_brick_list}")
            return ret

        self.logger.info(f"All bricks are online: {bricks_list}")
        return ret

    def check_if_bricks_list_changed(self,
                                     bricks_list: list,
                                     volname: str,
                                     node: str) -> bool:
        """
        Checks if the bricks list changed.

        Args:
            bricks_list: list of bricks
            volname: Name of volume
            node: Node on which to execute vol info

        Returns:
        bool: True if the list changed
              False if list didn't change
        """
        if not isinstance(bricks_list, list):
            bricks_list = [bricks_list]

        vol_info = self.get_volume_info(node, volname)

        vol_info_brick_list = []
        for n in vol_info[volname]['bricks']:
            vol_info_brick_list.append(n['name'])

        if len(vol_info_brick_list) == len(bricks_list):
            for each in bricks_list:
                if each not in vol_info_brick_list:
                    return True
            return False
        return True

    def get_all_bricks(self, volname: str, node: str) -> list:
        """
        Get list of all the bricks of the specified volume
        using the data from volume info.

        Args:
            volname (str): Name of the volume
            node (str): Node on which command has to be executed

        Returns:
            list: List of all the bricks of the volume on Success.
            NoneType: None on failure.
        """

        vol_info = self.get_volume_info(node, volname)
        if vol_info is None:
            self.logger.error(f"Unable to get "
                              f"the volinfo of {volname}.")
            return None

        # Get bricks from a volume
        all_bricks = []
        if 'bricks' in vol_info[volname]:
            for brick in vol_info[volname]['bricks']:
                if 'name' in brick:
                    all_bricks.append(brick['name'])
                else:
                    self.logger.error(f"Brick {brick} doesn't have the "
                                      f"key 'name' for the volume {volname}")
                    return None
            return all_bricks
        self.logger.error(f"Bricks not found in the volume {volname}")
        return None

    def get_online_bricks_list(self, volname: str, node: str) -> list:
        """
        Get list of bricks which are online.

        Args:
            volname (str): Name of the volume.
            node (str): Node on which commands will be executed.

        Returns:
            list : List of bricks in the volume which are online.
            NoneType: None on failure in getting volume status
        """
        online_bricks_list = []
        try:
            volume_status = self.get_volume_status(volname, node)
        except Exception as error:
            self.logger.info(f"Volume status failed: {error}")
            return None

        if not volume_status:
            self.logger.error(f"Unable to get online bricks_list "
                              f"for the volume {volname}")
            return None
        all_bricks = self.get_all_bricks(volname, node)

        volume_status = volume_status[volname]
        if 'node' in volume_status:
            for brick in volume_status['node']:
                if 'status' in brick:
                    if int(brick['status']) == 1:
                        cmp_brick_path = (f"{brick['hostname']}:"
                                          f"{brick['path']}")
                        if cmp_brick_path in all_bricks:
                            online_bricks_list.append(cmp_brick_path)
                else:
                    self.logger.error(f"Key 'status' not in brick: {brick}")
                    return None

            return online_bricks_list
        self.logger.error(f"Key 'node' not in volume status of {volname}")
        return None

    def get_offline_bricks_list(self, volname: str, node: str) -> list:
        """
        Get list of bricks which are offline. The list is created
        from the volume status information.

        Args:
            volname (str): Name of the volume.
            node (str): Node on which commands will be executed.

        Returns:
            list : List of bricks in the volume which are offline.
            NoneType: None on failure in getting volume status
        """
        offline_bricks_list = []
        all_bricks = self.get_all_bricks(volname, node)
        try:
            volume_status = self.get_volume_status(volname, node)
        except Exception as error:
            self.logger.info(f"Volume status failed: {error}")
            return all_bricks

        if not volume_status:
            self.logger.error(f"Unable to get offline bricks_list "
                              f"for the volume {volname}")
            return None

        volume_status = volume_status[volname]
        if 'node' in volume_status:
            for brick in volume_status['node']:
                if 'status' in brick:
                    cmp_brick_path = (f"{brick['hostname']}:"
                                      f"{brick['path']}")
                    if int(brick['status']) != 1:
                        if cmp_brick_path in all_bricks:
                            offline_bricks_list.append(cmp_brick_path)
                    elif int(brick['status']) == 1:
                        if cmp_brick_path in all_bricks:
                            all_bricks.remove(cmp_brick_path)
                else:
                    self.logger.error(f"Key 'status' not in brick: {brick}")
                    return None

            for brick in all_bricks:
                if brick not in offline_bricks_list:
                    offline_bricks_list.append(brick)

            return offline_bricks_list
        self.logger.error(f"Key 'node' not in volume status of {volname}")
        return None

    def wait_for_bricks_to_go_offline(self, volname: str, brick_list: list,
                                      timeout: int = 100) -> bool:
        """
        Function to wait till the given set of bricks in brick list go offline.

        Args:
            volname (str): Name of the volume whose bricks are to be noticed.
            brick_list (list): List of bricks which are to be brought down.
            timeout (int): Optional parameter with defailt value 100. The
                           function waits for these many seconds at max till
                           bricks go offline.

        Returns:
            True if the bricks go offline else False.
        """
        if not isinstance(brick_list, list):
            brick_list = [brick_list]

        nd_list = []
        for brickd in brick_list:
            if brickd.split(':')[0] not in nd_list:
                nd_list.append(brickd.split(':')[0])
        itr = 0
        while itr < timeout:
            random_node = random.choice(nd_list)
            offline_brick_list = self.get_offline_bricks_list(volname,
                                                              random_node)
            if offline_brick_list is not None and\
                    set(brick_list).issubset(set(offline_brick_list)):
                return True
            itr += 5
            sleep(5)
        self.logger.error(f"Current offline brick list : {offline_brick_list}"
                          " Compared to expected offline brick list :"
                          f" {brick_list}")
        return False

    def wait_for_bricks_to_come_online(self, volname: str, server_list: list,
                                       brick_list: list,
                                       timeout: int = 100) -> bool:
        """
        Function to wait till the given set of bricks in brick list come
        online.

        Args:
            volname (str): Name of the volume whose bricks are to be brought
                           online.
            server_list (list): A list of servers which are hosting the volume.
            brick_list (list): List of bricks which are to be brought up.
            timeout (int): Optional parameter with defailt value 100. The
                           function waits for these many seconds at max till
                           bricks come online.

        Returns:
            True if the bricks come online else False.
        """
        if not isinstance(brick_list, list):
            brick_list = [brick_list]

        itr = 0
        while itr < timeout:
            random_node = random.choice(server_list)
            online_brick_list = self.get_online_bricks_list(volname,
                                                            random_node)
            if online_brick_list is not None and\
                    set(brick_list).issubset(set(online_brick_list)):
                return True
            itr += 5
            sleep(5)

        self.logger.error(f"Current online brick list : {online_brick_list}"
                          " Compared to expected online brick list :"
                          f" {brick_list}")
        return False

    # TODO Brick mux logic inclusion.
    def bring_bricks_offline(self, volname: str, brick_list: list,
                             timeout: int = 100) -> bool:
        """
        Function to bring the given set of bricks offline.

        Args:
            volname (str): Name of the volume whose bricks are to be brought
                           down.
            brick_list (list): List of bricks which are to be brought down.
            timeout (int): Optional parameter with defailt value 100. The
            function waits for these many secondsat max till bricks go offline.

        Returns:
            True if the bricks are brought offline else False.
        """
        if not isinstance(brick_list, list):
            brick_list = [brick_list]

        self.logger.info(f"Getting {brick_list} offline.")
        nd_list = []
        for brick in brick_list:
            nd, path = brick.split(":")
            if nd not in nd_list:
                nd_list.append(nd)
            path = path.replace("/", "-")
            cmd = (f"pid=`ps -ef | grep -ve 'grep' | grep -e '{nd}{path}.pid' "
                   " | awk '{print $2}'` && kill -15 $pid || kill -9 $pid")
            ret = self.execute_abstract_op_node(cmd, nd, False)
            if ret['error_code'] != 0:
                self.logger.error(f"Failed to bring {brick_list} offline."
                                  f" As {cmd} failed on {nd}")
                return False

        # Wait till the said bricks come offline.
        return self.wait_for_bricks_to_go_offline(volname, brick_list, timeout)

    # TODO Brick mux logic inclusion.
    def bring_bricks_online(self, volname: str, server_list: list,
                            brick_list: list, disrup_method: bool = False,
                            timeout: int = 100) -> bool:
        """
        Function to bring the bricks belonging to a volume online. One can
        either use a disruptive mode to achive this or a non-disruptive way.

        Args:
            volname (str): Name of the volume whose bricks have to be brought
                           online.
            server_list (list): Nodes of the cluster.
            brick_list (list): The bricks which are offline.
            disrup_method (bool): Whether to use a disruptive way of starting
                                  the bricks using glusterd start or a non
                                  disruptive way of starting the bricks using
                                  volume start with force option.
            timeout (int): The timout till which we will check whether the
                           bricks have come online.

        Returns:
            True if the bricks are online else False.
        """
        if not isinstance(brick_list, list):
            brick_list = [brick_list]

        if not isinstance(server_list, list):
            server_list = [server_list]

        if not disrup_method:
            self.logger.info(f"Getting bricks {brick_list} online by forced"
                             f" volume start of {volname}")
            self.volume_start(volname, random.choice(server_list), True)
        else:
            self.logger.info(f"Getting bricks {brick_list} online by "
                             " glusterd restart in respective nodes.")
            node_list = []
            for bdata in brick_list:
                if bdata.split(':')[0] not in node_list:
                    node_list.append(bdata.split(':')[0])
            for nd in node_list:
                self.restart_glusterd(nd)
                self.wait_for_glusterd_to_start(nd)

        self.wait_till_all_peers_connected(server_list)

        # Wait till all said bricks are online.
        return self.wait_for_bricks_to_come_online(volname, server_list,
                                                   brick_list, timeout)

    def get_brick_processes_count(self, node: str) -> int:
        """
        Get the brick process count for a given node.

        Args:
            node (str): Node on which brick process has to be counted.

        Returns:
            int: Number of brick processes running on the node.
            None: If the command fails to execute.
        """
        ret = self.execute_abstract_op_node("pgrep -c glusterfsd", node,
                                            False)
        if ret['error_code'] == 0:
            count_of_proc = int(ret['msg'][0].rstrip('\n'))
            return count_of_proc
        else:
            return None

    def delete_bricks(self, bricks_list: list) -> bool:
        """
        Deleted list of bricks specified from the brick nodes.

        Args:
            bricks_list (list): List of bricks to be deleted.

        Returns:
            bool : True if all the bricks are deleted. False, otherwise.

        """
        if not isinstance(bricks_list, list):
            bricks_list = [bricks_list]

        _rc = True
        for brick in bricks_list:
            brick_node, brick_path = brick.split(":")
            self.execute_abstract_op_node(f"rm -rf {brick_path}",
                                          brick_node)
            ret = self.execute_abstract_op_node(f"ls {brick_path}",
                                                brick_node,
                                                False)
            if ret['error_code'] == 0:
                self.logger.error(f"Unable to delete brick {brick_path}"
                                  f" on node {brick_node}")
                _rc = False
        return _rc

    def is_broken_symlinks_present_on_bricks(self, node: str,
                                             volname: str) -> bool:
        """
        Checks if the backend bricks have broken symlinks.

        Args:
            node (str): Node on which command has to be executed.
            volname (str): Name of the volume

        Returns:
            (bool)True if present else False
        """
        brick_list = self.get_all_bricks(volname, node)
        for brick in brick_list:
            brick_node, brick_path = brick.split(":")
            cmd = f"find {brick_path} -xtype l | wc -l"
            ret = self.execute_abstract_op_node(cmd, brick_node,
                                                False)
            if ret['error_code'] != 0:
                self.logger.error(f"Failed to run the command {cmd}"
                                  f" on node {brick_node}")
                return True

            if len(ret['msg']) > 0:
                self.logger.error("Error: Broken symlink found on brick"
                                  f" path {brick_path} on {brick_node}")
                return True

        return False

    def umount_snap_brick_from_servers(self, nodes: list):
        """
        Method to umount the snap bricks in the servers.

        Args:
            nodes (list): List of nodes for which the snap brick has
            to be un-mounted.
        """
        cmd = ("for mnt in `mount | grep 'run/gluster/snaps' |"
               "awk '{print $3}'`;do umount $mnt; done")
        for node in nodes:
            self.execute_abstract_op_node(cmd, node)

    def get_bricks_to_bring_offline_from_replicated_volume(
        self,
        subvols_list: list,
        replica_count: int,
        quorum_info: dict
    ) -> list:
        """
        Randomly selects bricks to bring offline without affecting the cluster
        for a replicated volume.

        Args:
            subvols_list (list): list of subvols.
            replica_count (int): Replica count of a Replicate or
                                 Distributed-Replicate volume.
            quorum_info (dict): dict containing quorum info of the volume.
                                The dict should have the following info:
                              - is_quorum_applicable, quorum_type, quorum_count
        Returns:
            list: List of bricks that can be brought offline without
                  affecting the cluster. On any failure returns None.
        """
        list_of_bricks_to_bring_offline = []
        try:
            is_quorum_applicable = quorum_info['is_quorum_applicable']
            quorum_type = quorum_info['quorum_type']
            quorum_count = quorum_info['quorum_count']
        except KeyError:
            self.logger.error("Unable to get the proper quorum data "
                              f"from quorum info:{quorum_info}")
            return None

        # offline_bricks_limit: Maximum Number of bricks that can be offline
        # without affecting the cluster
        if is_quorum_applicable:
            if 'fixed' in quorum_type:
                if quorum_count is None:
                    self.logger.error("Quorum type is 'fixed' for"
                                      " the volume. But Quorum "
                                      "count not specified. Invalid Quorum")
                    return None
                else:
                    offline_bricks_limit = (
                        int(replica_count) - int(quorum_count))

            elif 'auto' in quorum_type:
                offline_bricks_limit = int(replica_count) // 2

            elif quorum_type is None:
                offline_bricks_limit = int(replica_count) - 1

            else:
                self.logger.error(f"Invalid Quorum Type : {quorum_type}")
                return None

            for subvol in subvols_list:
                random.shuffle(subvol)

                # select a random count.
                random_count = random.randint(1, offline_bricks_limit)

                # select random bricks.
                bricks_to_bring_offline = random.sample(subvol, random_count)

                # Append the list with selected bricks to bring offline.
                list_of_bricks_to_bring_offline.extend(bricks_to_bring_offline)

        return list_of_bricks_to_bring_offline

    def get_bricks_to_bring_offline_from_disperse_volume(
        self,
        subvols_list: list,
        redundancy_count: int
    ) -> list:
        """
        Randomly selects bricks to bring offline without
        affecting the cluster for a disperse volume.

        Args:
            subvols_list: list of subvols.
            redundancy_count: Redundancy count of a Disperse or
                              Distributed-Disperse volume.

        Returns:
            list: List of bricks that can be brought offline without
                  affecting the cluster.On any failure return None.
        """
        list_of_bricks_to_bring_offline = []
        for subvol in subvols_list:
            random.shuffle(subvol)

            # select a random value from 1 to redundancy_count.
            random_count = random.randint(1, int(redundancy_count))

            # select random bricks.
            bricks_to_bring_offline = random.sample(subvol, random_count)

            # Append the list with selected bricks to bring offline.
            list_of_bricks_to_bring_offline.extend(bricks_to_bring_offline)

            if list_of_bricks_to_bring_offline == []:
                return None

        return list_of_bricks_to_bring_offline

    def select_volume_bricks_to_bring_offline(self,
                                              volname: str,
                                              node: str) -> list:
        """
        Randomly selects bricks to bring offline without
        affecting the cluster

        Args:
            volname (str): Name of the volume.
            node (str): Node on which commands will be executed.

        Returns:
            list: On success returns a list of bricks bring offline.
                  If volume doesn't exist returns None.
        """
        volume_bricks_to_bring_offline = []

        # get volume type
        volume_type_info = self.get_volume_type_info(node, volname)
        if volume_type_info is None:
            return None
        volume_type = volume_type_info['volume_type_info']['typeStr']

        # get subvols
        volume_subvols = self.get_subvols(volname, node)

        # select bricks from distribute volume
        if volume_type == 'Distribute':
            volume_bricks_to_bring_offline = []

        # select bricks from replicated, distributed-replicated volume
        elif volume_type in ['Replicate', 'Distributed-Replicate']:
            # Get replica count
            volume_replica_count = (volume_type_info['volume_type_info']
                                    ['replicaCount'])

            # Get quorum info
            quorum_info = self.get_client_quorum_info(volname, node)
            volume_quorum_info = quorum_info['volume_quorum_info']

            # Get list of bricks to bring offline
            volume_bricks_to_bring_offline = (
                self.get_bricks_to_bring_offline_from_replicated_volume(
                    volume_subvols,
                    volume_replica_count,
                    volume_quorum_info))

        # select bricks from Disperse, Distribured-Disperse volume
        elif volume_type in ['Disperse', 'Distributed-Disperse']:
            # Get redundancy count
            volume_redundancy_count = (volume_type_info['volume_type_info']
                                       ['redundancyCount'])

            # Get list of bricks to bring offline
            volume_bricks_to_bring_offline = (
                self.get_bricks_to_bring_offline_from_disperse_volume(
                    volume_subvols, volume_redundancy_count))

        if volume_bricks_to_bring_offline == []:
            return None
        return volume_bricks_to_bring_offline
