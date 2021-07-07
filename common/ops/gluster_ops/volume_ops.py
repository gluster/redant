"""
This file contains one class - VolumeOps which
holds volume related APIs which will be called
from the test case.
"""
# pylint: disable=too-many-lines

from time import sleep

from common.ops.abstract_ops import AbstractOps


class VolumeOps(AbstractOps):
    """
    VolumeOps class provides APIs to perform operations
    related to volumes like mount,create,delete,start,stop,
    fetch information.
    """

    def setup_volume(self, volname: str, node: str, conf_hash: dict,
                     server_list: list, brick_root: dict,
                     force: bool = False, create_only: bool = False,
                     excep: bool = True):
        """
        Setup the gluster volume with specified configuration
        Args:
            volname(str): volume name that has to be created
            node(str): server on which command has to be executed
            conf_hash (dict): Config hash providing parameters for volume
                              creation.
            server_list (list): List of servers
            brick_root (dict): List of root path of bricks
            force (bool): If this option is set to True, then create volume
                          will get executed with force option.
            create_only (bool): True, if only volume creation is needed.
                                False, will do volume create, start, set
                                operation if any provided in the volume_config
                                By default, value is set to False.
            excep (bool): exception flag to bypass the exception if the
                          setup volume command fails. If set to False
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

        # Check if the volume already exists
        vollist = self.get_volume_list(node)
        if vollist is not None and volname in vollist:
            self.logger.info(f"Volume {volname} already exists.")
            return True

        # Create volume
        ret = self.volume_create(volname, node, conf_hash, server_list,
                                 brick_root, force, excep)
        if create_only:
            return ret

        if not excep and ret['error_code'] != 0:
            return ret

        # Start volume
        ret = self.volume_start(volname, node, excep)
        return ret

    def volume_create(self, volname: str, node: str, conf_hash: dict,
                      server_list: list, brick_root: dict,
                      force: bool = False, excep: bool = True):
        """
        Create the gluster volume with specified configuration
        Args:
            volname(str): volume name that has to be created
            node(str): server on which command has to be executed
            conf_hash (dict): Config hash providing parameters for volume
                              creation.
            server_list (list): List of servers
            brick_root (dict): List of root path of bricks
            force (bool): If this option is set to True, then create volume
                          will get executed with force option.
            excep (bool): exception flag to bypass the exception if the
                          volume create command fails. If set to False
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
        if not isinstance(server_list, list):
            server_list = [server_list]

        brick_cmd = ""
        mul_fac = 0
        cmd = ""
        brick_dict = {}
        if "replica_count" in conf_hash:
            mul_fac = conf_hash["replica_count"]

            if "arbiter_count" in conf_hash:
                mul_fac += conf_hash["arbiter_count"]

            if "dist_count" in conf_hash:
                mul_fac *= conf_hash["dist_count"]

        elif "dist_count" in conf_hash:
            mul_fac = conf_hash["dist_count"]

            if "disperse_count" in conf_hash:
                mul_fac *= conf_hash["disperse_count"]

        else:
            mul_fac = conf_hash["disperse_count"]

        brick_dict, brick_cmd = self.form_brick_cmd(server_list, brick_root,
                                                    volname, mul_fac)
        if "replica_count" in conf_hash and conf_hash['replica_count'] > 1:
            # arbiter vol and distributed-arbiter vol
            if "arbiter_count" in conf_hash:
                cmd = (f"gluster volume create {volname} "
                       f"replica {conf_hash['replica_count']} "
                       f"arbiter {conf_hash['arbiter_count']} {brick_cmd} "
                       "--mode=script")
            # replicated vol
            else:
                cmd = (f"gluster volume create {volname} "
                       f"replica {conf_hash['replica_count']}"
                       f" {brick_cmd} --mode=script")
        # dispersed vol and distributed-dispersed vol
        elif "disperse_count" in conf_hash:
            cmd = (f"gluster volume create {volname} disperse {mul_fac} "
                   f"redundancy {conf_hash['redundancy_count']} {brick_cmd} "
                   f"--mode=script")
        # distributed vol
        else:
            cmd = (f"gluster volume create {volname} {brick_cmd} "
                   "--mode=script")

        if force:
            cmd = (f"{cmd} force")

        ret = self.execute_abstract_op_node(cmd, node, excep)

        # Don't add data in case volume creation fails
        if ret['error_code'] == 0:
            self.es.set_new_volume(volname, brick_dict)
            self.es.set_vol_type(volname, conf_hash)

        return ret

    def volume_create_with_custom_bricks(self, volname: str, node: str,
                                         conf_hash: dict, brick_cmd: str,
                                         brick_dict: dict,
                                         force: bool = False,
                                         excep: bool = True):
        """
        Create the gluster volume with custom bricks configuration
        Args:
            volname(str): volume name that has to be created
            node(str): server on which command has to be executed
            conf_hash (dict): Config hash providing parameters for volume
                              creation.
            brick_cmd (str): Brick string to use for volume creation
            brick_dict (dict): Brick dict containing details of bricks used
                               to create volume
            force (bool): If this option is set to True, then create volume
                          will get executed with force option.
            excep (bool): exception flag to bypass the exception if the
                          volume create command fails. If set to False
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
        if "replica_count" in conf_hash and conf_hash['replica_count'] > 1:
            # arbiter vol and distributed-arbiter vol
            if "arbiter_count" in conf_hash:
                cmd = (f"gluster volume create {volname} "
                       f"replica {conf_hash['replica_count']} "
                       f"arbiter {conf_hash['arbiter_count']} {brick_cmd}"
                       " --mode=script")
            # replicated vol
            else:
                cmd = (f"gluster volume create {volname} "
                       f"replica {conf_hash['replica_count']}"
                       f" {brick_cmd} --mode=script")
        # dispersed vol and distributed-dispersed vol
        elif "disperse_count" in conf_hash:
            cmd = (f"gluster volume create {volname} "
                   f"{conf_hash['disperse_count']} redundancy "
                   f"{conf_hash['redundancy_count']} {brick_cmd}"
                   " --mode=script")
        # distributed vol
        else:
            cmd = (f"gluster volume create {volname} {brick_cmd} "
                   "--mode=script")

        if force:
            cmd = (f"{cmd} force")

        ret = self.execute_abstract_op_node(cmd, node, excep)

        # Don't add data in case volume creation fails
        if ret['error_code'] == 0:
            self.es.set_new_volume(volname, brick_dict)
            self.es.set_vol_type(volname, conf_hash)

        return ret

    def volume_start(self, volname: str, node: str = None,
                     force: bool = False, excep: bool = True):
        """
        Starts the gluster volume
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): Name of the volume to start
            excep (bool): exception flag to bypass the exception if the
                          volume sstart command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True

        Kwargs:
            force (bool): If this option is set to True, then start volume
                will get executed with force option. If it is set to False,
                then start volume will get executed without force option

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        """

        if force:
            cmd = f"gluster volume start {volname} force --mode=script --xml"
        else:
            cmd = f"gluster volume start {volname} --mode=script --xml"

        ret = self.execute_abstract_op_node(cmd, node, excep)

        if not excep and ret['msg']['opRet'] != '0':
            return ret

        self.es.set_volume_start_status(volname, True)

        return ret

    def volume_stop(self, volname: str, node: str = None, force: bool = False,
                    excep: bool = True):
        """
        Stops the gluster volume
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): Name of the volume to stop
            excep (bool): exception flag to bypass the exception if the
                          volume stop command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True
        Kwargs:
            force (bool): If this option is set to True, then start volume
                will get executed with force option. If it is set to False,
                then start volume will get executed without force option
        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        """

        if force:
            cmd = f"gluster volume stop {volname} force --mode=script --xml"
        else:
            cmd = f"gluster volume stop {volname} --mode=script --xml"

        ret = self.execute_abstract_op_node(cmd, node, excep)

        if ret['msg']['opRet'] == '0':
            self.es.set_volume_start_status(volname, False)

        return ret

    def volume_delete(self, volname: str, node: str = None,
                      excep: bool = True):
        """
        Deletes the gluster volume if given volume exists in
        gluster.
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): Name of the volume to delete
            excep (bool): exception flag to bypass the exception if the
                          volume delete command fails. If set to False
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

        cmd = f"gluster volume delete {volname} --mode=script --xml"

        ret = self.execute_abstract_op_node(cmd, node, excep)

        # Delete volume for volds only if the command succeded
        if ret['msg']['opRet'] == '0':
            self.es.remove_volume_data(volname)

        return ret

    def sanitize_volume(self, volname: str, server_list: list,
                        client_list: list, brick_root: dict, vol_param: dict):
        """
        Sanitizing of the volume will be getting the volume
        ready for the next test case to be used (ND tests)
        or even within a test case for maybe some untold
        and strange scenario.
        Args:
            volname (str): Name of the volume to be sanitized.
            server_list (list) : A list of strings consisting of server IPs.
            client_list (list) : A list of strings consisting of client IPs.
            brick_root (dict) : The mapping of the brick roots with the
                                nodes.
            vol_param (dict) : Raw recipe for creating volume
        """
        # Check if the volume exists.
        if not self.es.does_volume_exists(volname):
            # A test case is for sure doing what it isn't supposed to..
            # But the framework here takes the higher ground and handles
            # things for the betterment of all TCs.
            self.setup_volume(volname, server_list[0], vol_param, server_list,
                              brick_root, force=True)

        # Check if the volume is started.
        if not self.es.get_volume_start_status(volname):
            self.volume_start(volname, server_list[0])

        # Perform volume reset.
        self.reset_volume_option(volname, 'all', server_list[0])

        # Check if the volume is mounted on a client.
        if self.es.get_mnt_pts_dict_in_list(volname) == []:
            # Check if mount dir exists in the node.
            mountdir = f"/mnt/{volname}"
            for node in client_list:
                self.execute_abstract_op_node(f"umount {mountdir}", node)
                self.execute_abstract_op_node(f"mkdir -p {mountdir}", node)
                self.volume_mount(server_list[0], volname, mountdir, node)

        # Clear out the mountpoint data.
        mount_list = self.es.get_mnt_pts_dict_in_list(volname)
        for mntd in mount_list:
            self.execute_abstract_op_node(f"rm -rf {mntd['mountpath']}/*",
                                          mntd['client'])

        # Check if the post test volume is same as that of pre test volume.
        ret = self.es.get_vol_type_changes(volname, vol_param)
        if ret:
            # It seems like something has gone awry, so do a volume
            # cleanup followed by setup volume.
            self.cleanup_volume(volname, server_list[0])
            self.setup_volume(volname, server_list[0], vol_param, server_list,
                              brick_root, force=True)

            # Check if the volume is mounted on a client.
            if self.es.get_mnt_pts_dict_in_list(volname) == []:
                # Check if mount dir exists in the node.
                mountdir = f"/mnt/{volname}"
                for node in client_list:
                    self.execute_abstract_op_node(f"mkdir -p {mountdir}", node)
                    self.volume_mount(server_list[0], volname, mountdir, node)

    def cleanup_volume(self, volname: str, node: str):
        """
        Cleanup volume will delete the volume and its mountpoints.
        Args:
            volname (str): Name of the volume to be sanitized.
            node (str) : Node on which the commands are run.
        """
        # Check if the volume exists.
        if self.es.does_volume_exists(volname):
            # Check if the volume is started.
            if not self.es.get_volume_start_status(volname):
                self.volume_start(volname, node)

            # Check if the volume is mounted on a client.
            if not self.es.get_mnt_pts_dict_in_list(volname) == []:
                # Check if mount dir exists in the node.
                mounts = self.es.get_mnt_pts_dict_in_list(volname)
                for mntd in mounts:
                    mount = mntd['mountpath']
                    # There might be a scenario wherein the mountpoint has
                    # been deleted. Hence stat to check if the mountpoint
                    # even exists. Also, we need to check if the mountpoint
                    # is able to connect to the bricks. There might be a
                    # Transport endpoint error too. But we can just unmount
                    # and remove the values in that scenario.
                    cmd = (f"stat {mount}")
                    ret = self.execute_abstract_op_node(cmd, mntd['client'],
                                                        False)
                    transport_error = "Transport endpoint is not connected"
                    if ret['error_code'] != 0:
                        if transport_error not in ret['error_msg']:
                            continue
                    # One more scenario we have here is when the directory
                    # was unmount but the data structure isn't updated. Hence
                    # the unmout shouldn't be a strict check.
                    self.volume_unmount(volname, mount, mntd['client'], False)
                    self.execute_abstract_op_node(f"rm -rf {mount}",
                                                  mntd['client'])
            self.volume_stop(volname, node, True)

            # Get the brick list of the volume to delete them
            brick_list = self.get_all_bricks(volname, node)

            # Delete the volume
            self.volume_delete(volname, node)

            # Delete the bricks
            self.delete_bricks(brick_list)

    def expand_volume(self, node: str, volname: str, server_list: list,
                      brick_root: dict, force: bool = False,
                      **kwargs) -> bool:
        """Forms list of bricks to add and adds those bricks to the volume.

        Args:
            node (str): Node on which commands has to be executed
            volname (str): volume name
            servers (str|list): A server|List of servers in the storage pool.

        Optional:
            force (bool): If the operation should be executed with force
            **kwargs:
                The keys, values in kwargs are:
                - replica_count : (int)|None.
                    Increase the current_replica_count by replica_count
                - distribute_count: (int)|None.
                    Increase the current_distribute_count by distribute_count
                - arbiter_count : (int)|None

        Returns:
            bool: True of expanding volumes is successful.
                  False otherwise.

        """
        bricks_cmd = self.form_brick_cmd_to_add_brick(node, volname,
                                                      server_list, brick_root,
                                                      **kwargs)

        if not bricks_cmd:
            self.logger.error("Unable to get bricks list to add-bricks. "
                              f"Hence unable to expand volume : {volname}")
            return False

        if 'replica_count' in kwargs:
            replica_count = kwargs['replica_count']

            # Get replica count info.
            current_replica_count = self.get_replica_count(node, volname)
            kwargs['replica_count'] = current_replica_count + replica_count

        # Add bricks to the volume
        self.logger.info(f"Adding bricks to the volume: {volname}")
        ret = self.add_brick(volname, bricks_cmd, node, force,
                             False, **kwargs)
        if ret['msg']['opRet'] != '0':
            self.logger.error("Failed to add bricks to the volume:"
                              f" {ret['msg']['opErrstr']}")
            return False

        dist_count = None
        if 'distribute_count' in kwargs:
            dist_count = int(kwargs['distribute_count'])
            self.es.set_vol_type_param(volname, 'dist_count', dist_count)

        rep_count = None
        if 'replica_count' in kwargs:
            rep_count = int(kwargs['replica_count'])
            self.es.set_vol_type_param(volname, 'replica_count', rep_count)

        if dist_count is None and rep_count is None:
            dist_count = 1
            self.es.set_vol_type_param(volname, 'dist_count', dist_count)

        self.logger.info(f"Successful in expanding the volume {volname}")
        return True

    def shrink_volume(self, node: str, volname: str, subvol_num: list = None,
                      replica_num: list = None, force: bool = False,
                      rebal_timeout: int = 300, delete_bricks: bool = True,
                      **kwargs) -> bool:
        """
        Remove bricks from the volume.

        Args:
            node (str): Node on which commands has to be executed
            volname (str): volume name

        Optional:
            subvol_num (int|list): int|List of sub volumes number to remove.
                For example: If subvol_num = [2, 5], Then we will be removing
                bricks from 2nd and 5th sub-volume of the given volume.
                The sub-volume number starts from 0.

            replica_num (int|list): int|List of replica leg to remove.
                If replica_num = 0, then 1st brick from each subvolume is
                removed the replica_num starts from 0.

            force (bool): If this option is set to True, then remove-brick
                command will get executed with force option. If it is set to
                False, then remove-brick is executed with 'start' and 'commit'
                when the remove-brick 'status' becomes completed.

            rebalance_timeout (int): Wait time for remove-brick to complete in
                seconds. Default is 5 minutes.

            delete_bricks (bool): After remove-brick delete the removed bricks.

        Kwargs:
            **kwargs: The keys, values in kwargs are:
                    - replica_count : (int)|None. Specify the replica count to
                        reduce
                    - distribute_count: (int)|None. Specify the distribute
                        count to reduce.

        Returns:
            bool: True if removing bricks from the volume is successful.
                False otherwise.

        """
        # pylint: disable=too-many-return-statements
        # Form bricks list to remove-bricks
        bricks_list_to_remove = (self.form_bricks_list_to_remove_brick(node,
                                 volname, subvol_num, replica_num,
                                 **kwargs))

        if bricks_list_to_remove is None:
            self.logger.error("Failed to form bricks list to remove-brick. "
                              f"Hence unable to shrink volume {volname}")
            return False

        replica_count = None
        current_replica_count = None
        if replica_num is not None or 'replica_count' in kwargs:
            if 'replica_count' in kwargs:
                replica_count = int(kwargs['replica_count'])
            if replica_num is not None:
                if isinstance(replica_num, int):
                    replica_count = 1
                else:
                    replica_count = len(replica_num)

            # Get replica count info.
            current_replica_count = self.get_replica_count(node, volname)

            replica_count = current_replica_count - replica_count

            if subvol_num is not None or 'distribute_count' in kwargs:
                force = False
            else:
                force = True

        # If force, then remove-bricks with force option
        if force:

            self.logger.info(f"Removing bricks {bricks_list_to_remove} from "
                             f"volume {volname} with force option")
            ret = self.remove_brick(node, volname, bricks_list_to_remove,
                                    "force", replica_count, False)
            if ret['msg']['opRet'] != '0':
                self.logger.error("Failed to remove bricks "
                                  f"{bricks_list_to_remove} from the volume "
                                  f"{volname} with force option")
                return False

            self.logger.info("Successfully removed bricks "
                             f"{bricks_list_to_remove} from the volume "
                             f"{volname} with force option")
            return True

        # remove-brick start
        self.logger.info(f"Start Removing bricks {bricks_list_to_remove} from"
                         f" the volume {volname}")
        ret = self.remove_brick(node, volname, bricks_list_to_remove,
                                "start", replica_count, False)
        if ret['msg']['opRet'] != '0':
            self.logger.error("Failed to start remove brick of bricks "
                              f"{bricks_list_to_remove} on the volume "
                              f"{volname}")
            return False
        self.logger.info("Successfully started removal of bricks "
                         f"{bricks_list_to_remove} from the volume {volname}")

        # remove-brick status
        self.logger.info("Logging remove-brick status of bricks "
                         f"{bricks_list_to_remove} on the volume {volname}")
        self.remove_brick(node, volname, bricks_list_to_remove,
                          "status", replica_count, False)

        # Wait for rebalance started by remove-brick to complete
        _rc = False
        while rebal_timeout > 0:
            ret = self.remove_brick(node, volname, bricks_list_to_remove,
                                    "status", replica_count, False)
            if ret['msg']['opRet'] != '0':
                self.logger.error("Failed to get remove-brick status of "
                                  f"bricks {bricks_list_to_remove} on volume"
                                  f"{volname}")
                return False

            status = ""
            if ret['msg']['volRemoveBrick'] is not None:
                status = ret['msg']['volRemoveBrick']['aggregate']['statusStr']

            if status == "completed":
                _rc = True
            elif status == "in progress":
                rebal_timeout = rebal_timeout - 30
                sleep(30)
            else:
                self.logger.error("Invalid status string in remove brick"
                                  " status")
                return False

            if _rc:
                break

        if not _rc:
            self.logger.error("Rebalance started by remove-brick is not yet "
                              f"complete on the volume {volname}")
            return False

        self.logger.info("Rebalance started by remove-brick is successfully "
                         f"complete on the volume {volname}")

        # remove-brick status after rebalance is complete
        self.logger.info("Checking remove-brick status of bricks "
                         f"{bricks_list_to_remove} on the volume {volname}"
                         "after rebalance is complete")

        ret = self.remove_brick(node, volname, bricks_list_to_remove,
                                "status", replica_count, False)
        if ret['msg']['opRet'] != '0':
            self.logger.error("Failed to get remove-brick status of "
                              f"bricks {bricks_list_to_remove} on volume"
                              f"{volname} after rebalance is complete")
            return False

        # Commit remove-brick
        self.logger.info("Commit remove-brick of bricks "
                         f"{bricks_list_to_remove} on volume {volname}")
        ret = self.remove_brick(node, volname, bricks_list_to_remove,
                                "commit", replica_count, False)
        if ret['msg']['opRet'] != '0':
            self.logger.error("Failed to commit remove-brick of bricks "
                              f"{bricks_list_to_remove} on volume {volname}")
            return False
        self.logger.info("Successfully committed remove-bricks of bricks "
                         f"{bricks_list_to_remove} on volume {volname}")

        # Delete the removed bricks
        if delete_bricks:
            ret = self.delete_bricks(bricks_list_to_remove)
            if not ret:
                return False

        dist_count = None
        if 'distribute_count' in kwargs:
            dist_count = int(kwargs['distribute_count'])
            self.es.set_vol_type_param(volname, 'dist_count', -dist_count)

        rep_count = None
        if replica_count is not None:
            rep_count = current_replica_count - replica_count
            self.es.set_vol_type_param(volname, 'replica_count', -rep_count)

        if dist_count is None and rep_count is None:
            dist_count = 1
            self.es.set_vol_type_param(volname, 'dist_count', -dist_count)

        return True

    def get_volume_info(self, node: str = None, volname: str = 'all',
                        excep: bool = True) -> dict:
        """
        Gives volume information
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
            excep (bool): exception flag to bypass the exception if the
                          volume info command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True
        Returns:
            dict: a dictionary with volume information.
        Example:
            get_volume_info(server)
         >>>{'test-vol1': {
                            'id': '6c0053a5-d11c-4ba0-ae5e-f5d5e43a4116',
                            'status': '0',
                            'statusStr': 'Created',
                            'snapshotCount': '0',
                            'brickCount': '2',
                            'bricks': [{
                                         'name': 'server-vm1:/brick1',
                                         'isArbiter': '0',
                                         '#text': 'server-vm1:/brick1'
                                         'hostUuid': '56d8....'
                                        },
                                        {'name': 'server-vm1:/brick3',
                                         'isArbiter': '0',
                                         '#text': 'server-vm1:/brick3'
                                         'hostUuid': '56d8....'
                                         }],
                            'optCount': '4',
                            'options': {
                                         'storage.fips-mode-rchecksum': 'on',
                                         'transport.address-family': 'inet',
                                         'nfs.disable': 'on',
                                         'snap-activate-on-create': 'enable'}
                          },
             'test-vol2': {
                            'id': 'd5b365b5-10f6-46db-a72d-259859c413af',
                            'status': '0',
                            'statusStr': 'Created',
                            'snapshotCount': '0',
                            'brickCount': '1',
                            'bricks': [{
                                         'name': 'server-vm1:/brick2',
                                         'isArbiter': '0',
                                         '#text': 'server-vm1:/brick2'
                                         'hostUuid': '56d8....'
                                        }],
                            'optCount': '4',
                            'options': {
                                         'storage.fips-mode-rchecksum': 'on',
                                         'transport.address-family': 'inet',
                                         'nfs.disable': 'on',
                                         'snap-activate-on-create': 'enable'
                                        }
                          }
            }

        """

        cmd = f"gluster volume info {volname} --xml"

        ret = self.execute_abstract_op_node(cmd, node, excep)

        if not excep and ret['msg']['opRet'] != '0':
            return ret

        volume_info = ret['msg']['volInfo']['volumes']
        ret_dict = {}
        if volume_info['count'] == '0':
            return ret_dict
        volume_list = volume_info['volume']
        if not isinstance(volume_list, list):
            volume_list = [volume_list]
        for volume in volume_list:
            for key, val in volume.items():
                if key == 'name':
                    volname = val
                    ret_dict[volname] = {}
                elif key == 'bricks':
                    ret_dict[volname]['bricks'] = []
                    brick_list = val['brick']
                    if not isinstance(brick_list, list):
                        brick_list = [brick_list]
                    for brick in brick_list:
                        brick_info = {}
                        for b_key, b_val in brick.items():
                            brick_info[b_key] = b_val
                        ret_dict[volname]['bricks'].append(brick_info)
                elif key == 'options':
                    ret_dict[volname]['options'] = {}
                    for option in val['option']:
                        for opt, opt_val in option.items():
                            if opt == 'name':
                                opt_name = opt_val
                            elif opt == 'value':
                                opt_value = opt_val
                        ret_dict[volname]['options'][opt_name] = opt_value
                else:
                    ret_dict[volname][key] = val

        return ret_dict

    def get_volume_type_info(self, node: str, volname: str) -> dict:
        """
        Returns volume type information for the specified volume.

        Args:
            node (str): Node on which commands are executed.
            volname (str): Name of the volume.

        Returns:
            dict : Dict containing the keys, values defining the volume type:
                Example:
                    volume_type_info = {
                        'volume_type_info': {
                            'typeStr': 'Disperse',
                            'replicaCount': '1',
                            'arbiterCount': '0',
                            'stripeCount': '1',
                            'disperseCount': '3',
                            'redundancyCount': '1'
                        }
                    }

                    volume_type_info = {
                        'volume_type_info': {}

            NoneType: None if volume does not exist or any other key errors.
        """
        volinfo = self.get_volume_info(node, volname, False)
        if not volinfo and 'msg' in volinfo.keys():
            return None

        volume_type_info = {'volume_type_info': {}}
        all_volume_type_info = {
            'typeStr': '',
            'replicaCount': '',
            'arbiterCount': '',
            'stripeCount': '',
            'disperseCount': '',
            'redundancyCount': ''
        }
        for key in all_volume_type_info.keys():
            if key in volinfo[volname]:
                all_volume_type_info[key] = volinfo[volname][key]
            else:
                self.logger.error(f"Unable to find key {key} in the volume"
                                  f" info for the volume {volname}")
                all_volume_type_info[key] = None

        volume_type_info['volume_type_info'] = all_volume_type_info

        return volume_type_info

    def get_replica_count(self, node: str, volname: str) -> int:
        """Get the replica count of the volume

        Args:
            node (str): Node on which commands are executed.
            volname (str): Name of the volume.

        Returns:
            int : Replica count of the volume.
            NoneType: None if it is parse failure.
        """
        vol_type_info = self.get_volume_type_info(node, volname)
        if vol_type_info is None:
            self.logger.error("Unable to get the replica count info for the"
                              f" volume {volname}")
            return None

        return int(vol_type_info['volume_type_info']['replicaCount'])

    def is_volume_started(self, volname: str, node: str) -> bool:
        """
        Function provides the state of the volume as whether started or stopped
        in boolean.

        Args:
            volname (str): Name of the volume
            node: (str): Node wherein the command is to be executed.

        Returns:
            boolean value. True if started, else False.
        """
        vol_status = self.get_volume_info(node, volname)[volname]['statusStr']
        if vol_status == 'Started':
            return True
        return False

    def wait_for_vol_to_go_offline(self, volname: str, node: str,
                                   timeout: int = 120) -> bool:
        """
        Function to wait till the said volume goes offline.

        Args:
            volname (str): Name of the volume.
            node (str): Node wherein the status will be checked.
            timeout (int): Optional parameter with default value of 120. We
                           will wait for at max 120 seconds before exiting the
                           function.

        Returns:
            True if offline else False.
        """
        itr = 0
        while itr < timeout:
            if not self.is_volume_started(volname, node):
                return True
            itr += 5
            sleep(5)
        return False

    def wait_for_vol_to_come_online(self, volname: str, node: str,
                                    timeout: int = 120) -> bool:
        """
        Function to wait till the said volume comes online.

        Args:
            volname (str): Name of the volume.
            node (str): Node wherein the status will be checked.
            timeout (int): Optional parameter with default value of 120. We
                           will wait for at max 120 seconds before exiting the
                           function.

        Returns:
            True if online else False.
        """
        itr = 0
        while itr < timeout:
            if self.is_volume_started(volname, node):
                return True
            itr += 5
            sleep(5)
        return False

    def get_volume_list(self, node: str = None) -> list:
        """
        Fetches the volume names in the gluster.
        Uses xml output of volume list and parses it into to list
        Args:
            node (str): Node on which cmd has to be executed.
        Returns:
            list: List of volume names
        Example:
            get_volume_list(server)
            >>>['testvol1', 'testvol2']
        """
        cmd = "gluster volume list --xml"

        ret = self.execute_abstract_op_node(cmd, node)

        volume_list_count = int(ret['msg']['volList']['count'])
        volume_list = []
        if volume_list_count != 0:
            volume_list = ret['msg']['volList']['volume']

        if not isinstance(volume_list, list):
            volume_list = [volume_list]

        return volume_list

    def volume_reset(self, volname: str, node: str = None,
                     force: bool = False, excep: bool = True) -> dict:
        """
        Resets the gluster volume of all the reconfigured options.
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): Name of the volume to reset

        Optional:
            force (bool): If this option is set to True, then reset volume
                will get executed with force option. If it is set to False,
                then reset volume will get executed without force option
            excep (bool): exception flag to bypass the exception if the
                          volume reset command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True
        Example:
            volume_reset("testvol",server)

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        """
        if force:
            cmd = f"gluster volume reset {volname} force --mode=script --xml"
        else:
            cmd = f"gluster volume reset {volname} --mode=script --xml"

        ret = self.execute_abstract_op_node(cmd, node, excep)

        return ret

    def get_volume_status(self, volname: str = 'all', node: str = None,
                          service: str = '', options: str = '',
                          excep: bool = True) -> dict:
        """
        Gets the status of all or the specified volume
        Args:
            node (str): Node on which cmd has to be executed.
        Kwargs:
            volname (str): volume name. Defaults to 'all'
            service (str): name of the service to get status.
                service can be, [nfs|shd|<BRICK>|quotad]], If not given,
                the function returns all the services
            options (str): options can be,
                [detail|clients|mem|inode|fd|callpool|tasks]. If not given,
                the function returns the output of gluster volume status
            excep (bool): exception flag to bypass the exception if the
                          volume status command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True

        Returns:
            dict: volume status in dict of dictionary format
            None: In case no volumes are present
        Example:
            get_volume_status("test-vol1",server)
         >>>{ 'test-vol1': {
                             'nodeCount': '2',
                             'node': [{
                                        'hostname': 'server-vm1',
                                        'path': '/brick1',
                                        'status': '1',
                                        'port': '49152',
                                        'ports': {
                                                   'tcp': '49152',
                                                   'rdma': 'N/A'
                                                 },
                                        'pid': '669291'
                                      },
                                      {
                                        'hostname': 'server-vm1',
                                        'path': '/brick3',
                                        'status': '1',
                                        'port': '49153',
                                        'ports': {
                                                   'tcp': '49153',
                                                   'rdma': 'N/A'
                                                  },
                                        'pid': '669307'
                                      }],
                             'tasks': None
                           }
            }
        """
        ret = {}

        cmd = f"gluster volume status {volname} {service} {options} --xml"
        ret = self.execute_abstract_op_node(cmd, node, excep)
        if not excep and ret['msg']['opRet'] != '0':
            return ret

        volume_status = ret['msg']['volStatus']['volumes']

        if volume_status is None:
            return None

        ret_dict = {}
        volume_list = volume_status['volume']
        if not isinstance(volume_list, list):
            volume_list = [volume_list]
        for volume in volume_list:
            for key, val in volume.items():
                if key == 'volName':
                    volname = val
                    ret_dict[volname] = {}
                elif key == 'node':
                    ret_dict[volname]['node'] = []
                    node_list = val
                    if not isinstance(node_list, list):
                        node_list = [node_list]
                    for node_i in node_list:
                        node_info = {}
                        check_flag = False
                        for n_key, n_val in node_i.items():
                            if n_key == 'hostname' and\
                                n_val in ['Snapshot Daemon', 'Bitrot Daemon',
                                          'Scrubber Daemon',
                                          'Self-heal Daemon']:
                                check_flag = True
                            if n_key == 'ports':
                                port_info = {}
                                for p_key, p_val in n_val.items():
                                    port_info[p_key] = p_val
                                node_info[n_key] = port_info
                            elif n_key == 'path' and n_val == 'localhost':
                                node_info[n_key] = node
                            elif check_flag and n_key == 'path':

                                ip_val = self.convert_hosts_to_ip(n_val,
                                                                  node)
                                node_info[n_key] = ip_val[0]
                                check_flag = False
                            else:
                                node_info[n_key] = n_val
                        ret_dict[volname]['node'].append(node_info)
                elif key == 'tasks':
                    nodename = 'task_status'
                    if val is None:
                        ret_dict[volname][nodename] = None
                        continue
                    if not isinstance(val, list):
                        tasks = [val]
                    for task in tasks:
                        if 'task' in list(task.keys()):
                            if nodename not in list(ret_dict[volname].keys()):
                                ret_dict[volname][nodename] = [task['task']]
                            else:
                                ret_dict[volname][nodename].append(
                                    task['task'])
                        else:
                            ret_dict[volname][nodename] = [task]
                else:
                    ret_dict[volname][key] = val

        return ret_dict

    def get_volume_options(self, volname: str = 'all', option: str = 'all',
                           node: str = None, excep: bool = True) -> dict:
        """
        Gets the option values for a given volume.
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
        Kwargs:
            option (str): volume option to get status.
                        If not given, the function returns all the options for
                        the given volume
            excep (bool): exception flag to bypass the exception if the
                          get volume options command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True
        Returns:
            dict: value for the given volume option in dict format, on success
            NoneType: on failure
        Example:
            get_volume_options(server)
         >>>{ 'cluster.server-quorum-ratio': '51 (DEFAULT)',
              'cluster.enable-shared-storage': 'disable (DEFAULT)',
              'cluster.op-version': '100000',
              'cluster.max-op-version': '100000',
              'cluster.brick-multiplex': 'disable (DEFAULT)',
              'cluster.max-bricks-per-process': '250 (DEFAULT)',
              'glusterd.vol_count_per_thread': '100 (DEFAULT)',
              'cluster.localtime-logging': 'disable (DEFAULT)',
              'cluster.daemon-log-level': 'INFO (DEFAULT)',
              'cluster.brick-graceful-cleanup': 'disable (DEFAULT)'
            }
        """

        cmd = f"gluster volume get {volname} {option} --xml --mode=script"

        ret = self.execute_abstract_op_node(cmd, node, excep)
        if ret['error_code'] != 0:
            return ret
        volume_options = ret['msg']['volGetopts']

        ret_dict = {}
        option_list = volume_options['Opt']
        if not isinstance(option_list, list):
            option_list = [option_list]
        for option_i in option_list:
            option_name = option_i['Option']
            option_value = option_i['Value']
            ret_dict[option_name] = option_value

        return ret_dict

    def set_volume_options(self, volname: str, options: dict,
                           node: str = None, multi_option: bool = False,
                           excep: bool = True):
        """
        Sets the option values for the given volume.
        Args:
            volname (str): volume name
            options (dict): volume options in key:value format
            node (str): Node on which cmd has to be executed.
            multi_option (bool): Set multiple options together for a
                                 volume/cluster
            excep (bool): To bypass or not to bypass the exception handling.
        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        Example:
            options = {"user.cifs":"enable","user.smb":"enable"}
            set_volume_options("test-vol1", options, server)
        """

        volume_options = options
        if 'group' in volume_options:
            group_options = volume_options.pop('group')
            if not isinstance(group_options, list):
                group_options = [group_options]
            for group_option in group_options:
                cmd = (f"gluster volume set {volname} group {group_option} "
                       "--mode=script --xml")
                ret = self.execute_abstract_op_node(cmd, node, excep)

        if multi_option:
            opt_str = ""
            for option in volume_options:
                opt_str += f"{option} {volume_options[option]} "

            cmd = (f"gluster volume set {volname} {opt_str} "
                   "--mode=script --xml")
            ret = self.execute_abstract_op_node(cmd, node, excep)
            if ret['msg']['opRet'] == '0':
                if volname != 'all':
                    self.es.set_vol_option(volname, volume_options)
                else:
                    self.es.set_vol_options_all(volume_options)
        else:
            for option in volume_options:
                cmd = (f"gluster volume set {volname} {option} "
                       f"{volume_options[option]} --mode=script --xml")

                ret = self.execute_abstract_op_node(cmd, node, excep)
                if ret['msg']['opRet'] == '0':
                    if volname != 'all':
                        self.es.set_vol_option(
                            volname,
                            {option: volume_options[option]})
                    else:
                        self.es.set_vol_options_all(
                            {option: volume_options[option]})

        return ret

    def validate_volume_option(self, volname: str, options: dict,
                               node: str = None):
        """
        Validate the volume options
        Args:
            node (str) : Node on which cmd has to be executed
            volname (str) : volume name
            option (dict) : dictionary of options which are to be validated.
        Returns:
            No value if success or else ValueError will be raised.
        """
        for (opt, val) in options.items():
            ret_val = self.get_volume_options(volname, opt, node)
            if ret_val[opt] != val:
                raise Exception(f"Option {opt} has value {ret_val[opt]}"
                                f" not {val}")

    def reset_volume_option(self, volname: str, option: str,
                            node: str = None, force: bool = False):
        """
        Resets the volume option
        Args:
            node (str): Node on which cmd has to be executed
            volname (str): volume name
            option (str): volume option
        Kwargs:
            force (bool): If this option is set to True, then reset volume
                          will get executed with force option. If it is set
                          to False, then reset volume will get executed
                          without force option.
        Example:
            reset_volume_option("test-vol1", "option", server)

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        """

        if force:
            cmd = (f"gluster volume reset {volname} {option} force"
                   "--mode=script --xml")
        else:
            cmd = f"gluster vol reset {volname} {option} --mode=script --xml"

        ret = self.execute_abstract_op_node(cmd, node)
        self.es.reset_volume_option(volname, option)

        return ret

    def volume_sync(self, hostname: str, node: str, volname: str = 'all'):
        """
        Sync the volume to the specified host
        Args:
            node (str): Node on which cmd has to be executed.
            hostname (str): host name to which volume has to be sync'ed
        Kwargs:
            volname (str): volume name. Defaults to 'all'.
        Example:
            volume_sync(volname="testvol",server)

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        """

        cmd = f"gluster volume sync {hostname} {volname} --mode=script --xml"

        ret = self.execute_abstract_op_node(cmd, node)

        return ret

    def is_distribute_volume(self, volname: str) -> bool:
        """
        Check if volume is a plain distributed volume

        Args:
            volname (str): Name of the volume.

        Returns:
            bool : True if the volume is distributed volume. False otherwise
            NoneType: None if volume does not exist.
        """
        volume_dict = self.es.get_volume_dict(volname)
        if volume_dict['voltype']['dist_count'] > 0 and\
                volume_dict['voltype']['replica_count'] == 1:
            return True
        return False

    def wait_for_volume_process_to_be_online(self, volname: str, node: str,
                                             server_list: list,
                                             timeout: int = 300) -> bool:
        """
        Waits for the volume's processes to be online until timeout

        Args:
            volname (str): Name of the volume.
            node (str): Node on which commands will be executed.
            server_list (list): List of servers

        Optional:
            timeout (int): timeout value in seconds to wait for all volume
                           processes to be online.

        Returns:
            bool: True if the volume's processes are online within timeout,
                  False otherwise
        """

        # Fetch the brick list of the volume
        brick_list = self.get_all_bricks(volname, node)
        if brick_list is None:
            self.logger.error(f"Failed to get brick list of volume {volname}")
            return False

        # Wait for bricks to be online
        bricks_online_status = (
            self.wait_for_bricks_to_come_online(volname, server_list,
                                                brick_list))
        if not bricks_online_status:
            self.logger.error(f"Failed to wait for the volume {volname} "
                              "processes to be online")
            return False

        # Wait for self-heal-daemons to be online
        self_heal_daemon_online_status = (
            self.wait_for_self_heal_daemons_to_be_online(volname, node,
                                                         timeout))
        if not self_heal_daemon_online_status:
            self.logger.error(f"Failed to wait for the volume {volname}"
                              " processes to be online")
            return False

        # TODO: Add any new process checks here

        self.logger.info(f"Volume {volname} processes are all online")
        return True

    def get_subvols(self, volname: str, node: str) -> list:
        """
        Get the subvolumes in the given volume

        Args:
            volname(str): Volname to get the subvolume for
            node(str): Node on which command has to be executed

        Returns:
            list: Empty list if no volumes, or else a list of sub volume
                  lists. Wherein each subvol list contains bricks belonging
                  to that subvol in node:brick_path format.
        """
        subvols = []

        volinfo = self.get_volume_info(node, volname)
        if volinfo:
            voltype = volinfo[volname]['typeStr']
            brick_list = volinfo[volname]['bricks']
            bricks = [x["name"] for x in brick_list if "name" in x]
            if voltype in ("Replicate", "Distributed-Replicate"):
                rep = int(volinfo[volname]['replicaCount'])
                subvol_list = [bricks[i:i + rep] for i in range(0,
                                                                len(bricks),
                                                                rep)]
                subvols = subvol_list
            elif voltype == 'Distribute':
                for brick in bricks:
                    subvols.append([brick])
            elif voltype in ('Disperse', 'Distributed-Disperse'):
                disp_count = int(volinfo[volname]['disperseCount'])
                subvol_list = ([bricks[i:i + disp_count]
                                for i in range(0, len(bricks), disp_count)])
                subvols = subvol_list
        return subvols

    def get_num_of_bricks_per_subvol(self, node: str, volname: str) -> int:
        """
        Returns number of bricks per subvol

        Args:
            node (str): Node on which commands are executed.
            volname (str): Name of the volume.

        Returns:
            int : Number of bricks per subvol
            NoneType: None if volume does not exist.
        """
        subvols_list = self.get_subvols(volname, node)
        if subvols_list:
            return len(subvols_list[0])

        return None

    def bulk_volume_creation(self, node: str, number_of_volumes: int,
                             volname: str, conf_hash: dict,
                             server_list: list, brick_roots: dict,
                             vol_prefix="mult_vol_",
                             force: bool = False,
                             create_only: bool = False,
                             excep: bool = True):
        """
        Creates the number of volumes user has specified.

        Args:
        node (str) : node on which command has to execute
        number_of_volumes (int) : number of volumes to create
        volname (str): Name  of the volume
        conf_hash (dict) : Config hash providing parameters for volume
                        creation.
        server_list (list): list of servers.
        brick_roots (dict): brick root dictionary.
        vol_prefix (str): Prefix to be added to the volume name.
        force (bool): True, If volume create command need to be executed
                            with force, False Otherwise. Defaults to False.
        create_only (bool): True, if only volume creation is needed.
                            False, will do volume create, start, set operation
                            if any provided in the volume_config.
                            By default, value is set to False.
        excep (bool): True. Flag to indicate whether the exception handling
                      will kick in the abstract ops or will it be disabled.

        Returns: (bool)
        True if all the volumes were created, false otherwise.
        """
        if not number_of_volumes > 1:
            self.logger.error("Number of volumes should be >1")
            return False

        for volume in range(number_of_volumes):
            bulkvolname = f"{vol_prefix}{volname}{str(volume)}"
            ret = self.setup_volume(bulkvolname, node,
                                    conf_hash, server_list,
                                    brick_roots, force,
                                    create_only, excep)
            if not excep and ret['error_code'] != 0:
                self.logger.error("Volume creation failed for the"
                                  f" volume {volname}")
                return False

        return True

    def log_volume_info_and_status(self, node: str,
                                   volname: str):
        """
        Logs volume info and status

        Args:
            node (str): Node on which the command
                        has to be executed.
            volname (str): Name of volume
        Returns:
            bool: Returns True if getting volume info and
            status is successful. False Otherwise.
        """
        ret = self.get_volume_info(node, volname, False)
        if 'msg' in ret.keys() and ret['msg']['opRet'] != '0':
            return False

        ret = self.get_volume_status(volname, node,
                                     excep=False)
        if 'msg' in ret.keys() and ret['msg']['opRet'] != '0':
            return False

        return True

    def is_volume_exported(self, node: str, volname: str,
                           share_type: str):
        """
        Checks whether the volume is exported as nfs
        or cifs share

        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
            share_type (str): nfs or cifs

        Returns:
            bool: If volume is exported returns True.
                False Otherwise.
        """
        if 'nfs' in share_type:
            cmd = "showmount -e localhost"
            self.execute_abstract_op_node(cmd, node)

            cmd = f"showmount -e localhost | grep -w {volname}"
            ret = self.execute_abstract_op_node(cmd,
                                                node,
                                                False)
            if ret['error_code'] != 0:
                return False

        if 'cifs' in share_type or 'smb' in share_type:
            cmd = "smbclient -L localhost"
            self.execute_abstract_op_node(cmd, node)

            cmd = ("smbclient -L localhost -U | "
                   f"grep -i -Fw gluster {volname}")
            ret = self.execute_abstract_op_node(cmd,
                                                node,
                                                False)
            if ret['error_code'] != 0:
                return False
        return True

    def verify_all_process_of_volume_are_online(self, volname: str,
                                                node: str) -> bool:
        """
        Verifies whether all the processes of volume are online

        Args:
            volname (str): volume name
            node (str): Node on which cmd has to be executed.

        Returns:
            bool: Returns True if all the processes of volume are online.
                  False Otherwise.
        """
        bricks_list = self.get_all_bricks(volname, node)
        if bricks_list is None:
            return False

        if not self.are_bricks_online(volname, bricks_list, node):
            return False

        # Verify all self-heal-daemons are running for non-distribute volumes.
        if not self.is_distribute_volume(volname):
            if not self.are_all_self_heal_daemons_online(volname,
                                                         node):
                return False

        return True

    def get_client_quorum_info(self, volname: str, node: str) -> dict:
        """
        Get the client quorum information. i.e the quorum type,
        quorum count.
        Args:
            volname (str): Name of the volume.
            node (str): Node on which commands are executed.

        Returns:
            dict: client quorum information for the volume.
                client_quorum_dict = {
                    'volume_quorum_info':{
                        'is_quorum_applicable': False,
                        'quorum_type': None,
                        'quorum_count': None
                        }
            }
        """
        client_quorum_dict = {
            'volume_quorum_info': {
                'is_quorum_applicable': False,
                'quorum_type': None,
                'quorum_count': None
            }
        }

        # get quorum-type
        volume_option = self.get_volume_options(volname,
                                                'cluster.quorum-type',
                                                node)
        if volume_option is None:
            self.logger.error("Unable to get the volume option "
                              f"'cluster.quorum-type' for volume {volname}")
            return client_quorum_dict
        quorum_type = volume_option['cluster.quorum-type']

        # get quorum-count
        volume_option = self.get_volume_options(volname,
                                                'cluster.quorum-count',
                                                node)
        if volume_option is None:
            self.logger.error("Unable to get the volume option "
                              f"'cluster.quorum-count' for volume {volname}")
            return client_quorum_dict
        quorum_count = volume_option['cluster.quorum-count']

        # set the quorum info
        volume_type_info = self.get_volume_type_info(node, volname)

        if volume_type_info is None:
            return client_quorum_dict

        volume_type = volume_type_info['volume_type_info']['typeStr']

        if volume_type in ['Replicate', 'Distributed-Replicate']:
            (client_quorum_dict['volume_quorum_info']
                ['is_quorum_applicable']) = True
            replica_count = (volume_type_info['volume_type_info']
                             ['replicaCount'])

            # Case1: Replica 2
            if int(replica_count) == 2:
                if 'none' not in quorum_type:
                    (client_quorum_dict['volume_quorum_info']
                        ['quorum_type']) = quorum_type

                    if quorum_type == 'fixed':
                        if not quorum_count == '(null)':
                            (client_quorum_dict['volume_quorum_info']
                                ['quorum_count']) = quorum_count

            # Case2: Replica > 2
            if int(replica_count) > 2:
                if quorum_type == 'none':
                    (client_quorum_dict['volume_quorum_info']
                        ['quorum_type']) = 'auto'
                elif quorum_type == 'fixed':
                    if not quorum_count == '(null)':
                        (client_quorum_dict['volume_quorum_info']
                            ['quorum_count']) = quorum_count
                else:
                    (client_quorum_dict['volume_quorum_info']
                        ['quorum_type']) = quorum_type

        return client_quorum_dict
