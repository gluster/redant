"""
Heal ops module deals with the functions related to heal related operations.
"""

from time import sleep


class HealOps:
    """
    Class which is responsible for methods for heal related operations.
    """

    def trigger_heal(self, volname: str, node: str):
        """
        This function triggers the heal operation

        Args:
        volname (str): Name of the volume
        node (str): Node on which command has to
                    be executed.
        Returns:
        bool : True if heal is triggered successfully. False otherwise.
        """
        cmd = f"gluster volume heal {volname}"
        ret = self.execute_abstract_op_node(cmd, node,
                                            False)
        if ret['error_code'] != 0:
            return False

        return True

    def wait_for_self_heal_daemons_to_be_online(self, volname: str, node: str,
                                                timeout: int = 300) -> bool:
        """
        Waits for the volume self-heal-daemons to be online until timeout

        Args:
            volname (str): Name of the volume.
            node (str): Node on which commands will be executed.

        Optional:
            timeout (int): timeout value in seconds to wait for
                           self-heal-daemons to be online.

        Returns:
            bool : True if all self-heal-daemons are online within timeout,
                   False otherwise
        """
        # Return True if the volume is pure distribute
        if self.is_distribute_volume(volname):
            self.logger.info(f"Volume {volname} is a distribute volume. "
                             "Hence not waiting for self-heal daemons "
                             "to be online")
            return True

        counter = 0
        flag = 0
        while counter < timeout:
            status = self.are_all_self_heal_daemons_online(volname, node)
            if status:
                flag = 1
                break
            if not status:
                sleep(10)
                counter = counter + 10

        if not flag:
            self.logger.error(f"All self-heal-daemons of the volume {volname}"
                              f" are not online even after {timeout//60}"
                              " minutes")
            return False
        else:
            self.logger.info(f"All self-heal-daemons of the volume {volname}"
                             " are online")
        return True

    def are_all_self_heal_daemons_online(self, volname: str,
                                         node: str) -> bool:
        """
        Verifies whether all the self-heal-daemons are online for the
        specified volume.

        Args:
            volname (str): volume name
            node (str): Node on which cmd has to be executed.

        Returns:
            bool : True if all the self-heal-daemons are online for the volume.
                   False otherwise.
            NoneType: None if unable to get the volume status
        """
        if self.is_distribute_volume(volname):
            self.logger.info(f"Volume {volname} is a distribute volume. "
                             "Hence not waiting for self-heal daemons "
                             "to be online")
            return True

        service = 'shd'
        failure_msg = ("Verifying all self-heal-daemons are online failed for "
                       f"volume {volname}")
        # Get volume status
        vol_status = self.get_volume_status(volname, node, service)
        if vol_status is None:
            self.logger.error(failure_msg)
            return None

        # Get all nodes from pool list
        all_nodes = self.nodes_from_pool_list(node)
        if not all_nodes:
            self.logger.error(failure_msg)
            return False

        online_status = True
        if 'node' in vol_status[volname]:
            for brick in vol_status[volname]['node']:
                if brick['hostname'] == "Self-heal Daemon":
                    if brick['status'] != '1':
                        online_status = False
                        break

        if online_status:
            self.logger.info("All self-heal Daemons are online")
            return True
        else:
            self.logger.error("Some of the self-heal Daemons are offline")
            return False

    def get_heal_info(self, node: str, volname: str) -> list:
        """
        From the xml output of heal info command get the heal info data.

        Args:
            node : Node on which commands are executed
            volname : Name of the volume

        Returns:
            NoneType: None if parse errors.
            list: list of dictionaries. Each element in the list is the
                  heal_info data per brick.
        """
        cmd = f"gluster volume heal {volname} info --xml"
        ret = self.execute_abstract_op_node(cmd, node, False)
        if ret['msg']['opRet'] != '0':
            self.logger.error("Failed to get the heal info xml output for"
                              f" the volume {volname}.Hence failed to get"
                              " the heal info summary.")
            return None

        return ret['msg']['healInfo']['bricks']['brick']

    def get_heal_info_summary(self, node: str, volname: str) -> dict:
        """
        From the xml output of heal info command  get heal info summary
        i.e Bricks and it's corresponding number of entries, status.

        Args:
            node : Node on which commands are executed
            volname : Name of the volume

        Returns:
            NoneType: None if parse errors.
            dict: dict of dictionaries. brick names are the keys of the
                  dict with each key having brick's status,
                  numberOfEntries info as dict.
                Example:
                    heal_info_summary_data = {
                        'ijk.lab.eng.xyz.com': {
                            'status': 'Connected'
                            'numberOfEntries': '11'
                            },
                        'def.lab.eng.xyz.com': {
                            'status': 'Transport endpoint is not connected',
                            'numberOfEntries': '-'
                            }
                        }
        """
        heal_info_data = self.get_heal_info(node, volname)
        if heal_info_data is None:
            self.logger.error("Unable to get heal info summary "
                              f"for the volume {volname}")
            return None

        heal_info_summary_data = {}
        for info_data in heal_info_data:
            heal_info_summary_data[info_data['name']] = {
                'status': info_data['status'],
                'numberOfEntries': info_data['numberOfEntries']
            }
        return heal_info_summary_data

    def is_heal_complete(self, node: str, volname: str) -> bool:
        """
        Verifies there are no pending heals on the volume.
        The 'number of entries' in the output of heal info
        for all the bricks should be 0 for heal to be completed.

        Args:
            node : Node on which commands are executed
            volname : Name of the volume

        Returns:
            bool: True if heal is complete. False otherwise
        """
        heal_info_data = self.get_heal_info(node, volname)
        if heal_info_data is None:
            self.logger.error("Unable to identify whether heal is"
                              f" successfull or not on volume {volname}")
            return False

        for brick_heal_info_data in heal_info_data:
            if brick_heal_info_data["numberOfEntries"] != '0':
                self.logger.error("Heal is not complete on some of the bricks"
                                  f" for the volume {volname}")
                return False

        self.logger.info("Heal is complete for all the bricks"
                         f" on the volume {volname}")
        return True

    def monitor_heal_completion(self, node: str, volname: str,
                                timeout_period: int = 1200,
                                bricks: list = None,
                                interval_check: int = 120) -> bool:
        """
        Monitors heal completion by looking into .glusterfs/indices/xattrop
        directory of every brick for certain time. When there are no entries
        in all the brick directories then heal is successful.
        Otherwise heal is pending on the volume.

        Args:
            node : Node on which commands are executed
            volname : Name of the volume
            timeout_period : time until which the heal monitoring to be done.
                             Default: 1200 i.e 20 minutes.
            bricks : list of bricks to monitor heal, if not provided
                    heal will be monitored on all bricks of volume
            interval_check : Time in seconds, for every given interval checks
                            the heal info, defaults to 120.

        Returns:
            bool: True if heal is complete within timeout_period.
            False otherwise
        """
        if timeout_period != 0:
            heal_monitor_timeout = timeout_period

        time_counter = heal_monitor_timeout
        self.logger.info("Heal monitor timeout is : "
                         f"{(heal_monitor_timeout / 60)} minutes")

        # Get all bricks
        bricks_list = bricks or self.get_all_bricks(volname, node)
        if bricks_list is None:
            self.logger.error("Unable to get the bricks list. Hence"
                              "unable to verify whether self-heal-daemon "
                              "process is running or not "
                              f"on the volume {volname}")

            return False

        while time_counter > 0:
            heal_complete = True

            for brick in bricks_list:
                brick_node, brick_path = brick.split(":")
                cmd = (f"ls -1 {brick_path}/.glusterfs/indices/xattrop/ | "
                       "grep -ve \"xattrop-\" | wc -l")
                ret = self.execute_abstract_op_node(cmd, brick_node, False)
                out = int((ret['msg'][0]).rstrip("\n"))
                if out != 0:
                    heal_complete = False
                    break
            if heal_complete:
                break
            sleep(interval_check)
            time_counter = time_counter - interval_check

        if heal_complete and bricks:
            # In EC volumes, check heal completion only on online bricks
            # and `gluster volume heal info` fails for an offline brick
            return True

        if heal_complete and not bricks:
            heal_completion_status = self.is_heal_complete(node, volname)

            if heal_completion_status:
                self.logger.info("Heal has successfully completed"
                                 f" on volume {volname}")

                return True

        self.logger.info(f"Heal has not yet completed on volume {volname}")

        for brick in bricks_list:
            brick_node, brick_path = brick.split(":")
            cmd = f"ls -1 {brick_path}/.glusterfs/indices/xattrop/ "
            self.execute_abstract_op_node(cmd, brick_node)
        return False

    def get_heal_info_split_brain(self, node: str, volname: str) -> list:
        """
        From the xml output of heal info aplit-brain command get
        the heal info data.

        Args:
            node : Node on which commands are executed
            volname : Name of the volume

        Returns:
            NoneType: None if parse errors.
            list: list of dictionaries. Each element in the list is the
                heal_info data per brick.
        """
        cmd = f"gluster volume heal {volname} info split-brain --xml"
        ret = self.execute_abstract_op_node(cmd, node, False)
        if ret['msg']['opRet'] != '0':
            self.logger.error("Failed to get the heal info xml output for"
                              f" the volume {volname}.Hence failed to get"
                              " the heal info summary.")
            return None

        return ret['msg']['healInfo']['bricks']['brick']

    def is_volume_in_split_brain(self, node: str, volname: str) -> bool:
        """
        Verifies there are no split-brain on the volume.
        The 'number of entries' in the output of heal info split-brain
        for all the bricks should be 0 for volume not to be in split-brain.

        Args:
            node : Node on which commands are executed
            volname : Name of the volume

        Return:
            bool: True if volume is in split-brain. False otherwise
        """
        heal_info_split_brain_data = self.get_heal_info_split_brain(node,
                                                                    volname)
        if heal_info_split_brain_data is None:
            self.logger.error(f"Unable to verify whether volume {volname}"
                              " is not in split-brain or not")
            return False

        for brick_heal_info_split_brain_data in heal_info_split_brain_data:
            if brick_heal_info_split_brain_data['numberOfEntries'] == '-':
                continue
            if brick_heal_info_split_brain_data['numberOfEntries'] != '0':
                self.logger.error(f"Volume {volname} is in split-brain state.")
                return True

        self.logger.info(f"Volume {volname} is not in split-brain state.")
        return False

    def get_self_heal_daemon_pid(self, nodes: str) -> tuple:
        """
        Checks if self-heal daemon process is running and
        return the process id's in dictionary format

        Args:
            nodes ( str|list ) : Node/Nodes of the cluster

        Returns:
            tuple : Tuple containing two elements (ret, glustershd_pids).
            The first element 'ret' is of type 'bool', True if and only if
            glustershd is running on all the nodes in the list and each
            node contains only one instance of glustershd running.
            False otherwise.

            The second element 'glustershd_pids' is of type dictonary and it
            contains the process ID's for glustershd
        """
        glustershd_pids = {}
        _rc = True

        if not isinstance(nodes, list):
            nodes = [nodes]
        # cmd = r"pgrep -f glustershd | grep -v ^$$\$"
        cmd = "ps aux | grep 'process-name glustershd' | grep -v grep | awk '{print $2}'"
        self.logger.info(f"Running {cmd} on nodes {nodes}")
        results = self.execute_abstract_op_multinode(cmd, nodes, False)
        for result in results:
            if result['error_code'] == 0:
                if len(result['msg']) == 1:
                    if not (result['msg'][0]).strip().rstrip("\n"):
                        self.logger.error("No self heal daemon process found"
                                          f" on node {result['node']}")
                        _rc = False
                        glustershd_pids[result['node']] = -1
                    else:
                        pid = (result['msg'][0]).rstrip('\n')
                        self.logger.info("Single self heal daemon process with"
                                         f" pid {pid}"
                                         f" found on node {result['node']}")
                        glustershd_pids[result['node']] = pid
                else:
                    self.logger.error("More than one self heal daemon process"
                                      f" found on node {result['node']}")
                    _rc = False
                    glustershd_pids[result['node']] = -1
            else:
                self.logger.error("Unable to get self heal daemon process"
                                  f" from node {result['node']}")
                _rc = False
                glustershd_pids[result['node']] = -1

        return _rc, glustershd_pids

    def is_shd_daemonized(self, nodes: str, timeout: int = 120) -> bool:
        """
        Wait for the glustershd process to release parent process.

        Args:
            nodes ( str|list ) : Node/Nodes of the cluster
            timeout (int): timeout value in seconds to wait for
            self-heal-daemons to be online.

        Returns:
            bool : True if glustershd releases its parent.
                   False Otherwise
        """
        counter = 0

        if not isinstance(nodes, list):
            nodes = [nodes]

        while counter < timeout:
            ret, _ = self.get_self_heal_daemon_pid(nodes)

            if ret:
                break

            self.logger.info("Retry after 3 sec to get"
                             " self-heal daemon process.....")
            sleep(3)
            counter = counter + 3

        if not ret:
            self.logger.error("Either No self heal daemon process found "
                              "or more than one self heal daemon process"
                              f" found even after {timeout/60.0} minutes")
        else:
            self.logger.info("Single self heal daemon process on"
                             f" all nodes {nodes}")
        return ret

    def is_shd_daemon_running(self, node: str,
                              server: str, volname: str) -> bool:
        """
        Verifies whether the shd daemon is up and running on a
        particular node by checking the existence of shd pid
        and parsing the get volume status output.

        Args:
            node (str): The first node in servers list
            server (str): The node to be checked for whether
            the glustershd process is up or not
            volname (str): Name of the volume created

        Returns:
            boolean: True if shd is running on the node,
            False, otherwise
        """
        # Get glustershd pid from node
        ret, glustershd_pids = self.get_self_heal_daemon_pid(server)
        if not ret and glustershd_pids[server] != -1:
            return False

        # Verifying glustershd process is no longer running from get status
        vol_status = self.get_volume_status(volname, node)
        if vol_status is None:
            return False
        for host in vol_status[volname]['node']:
            if (host['hostname'] == 'Self-heal Daemon'
               and host['path'] == server):
                return True
        return False

    def enable_self_heal_daemon(self, volname: str, node: str) -> bool:
        """
        Enables self-heal-daemon on a volume by setting volume option
        'self-heal-daemon' to value 'on'

        Args:
            volname : Name of the volume
            node : Node on which commands are executed

        Returns:
            bool : True if setting self_heal_daemon option to
                   'on' is successful. False otherwise.
        """
        cmd = f"gluster volume set {volname} self-heal-daemon on --xml"
        ret = self.execute_abstract_op_node(cmd, node, False)
        if ret['msg']['opRet'] != '0':
            return False

        return True

    def disable_self_heal_daemon(self, volname: str, node: str) -> bool:
        """
        Disables self-heal-daemon on a volume by setting volume option
        'self-heal-daemon' to value 'off'

        Args:
            volname : Name of the volume
            node : Node on which commands are executed

        Returns:
            bool : True if setting self_heal_daemon option to
                   'off' is successful. False otherwise.
        """
        cmd = f"gluster volume set {volname} self-heal-daemon off --xml"
        ret = self.execute_abstract_op_node(cmd, node, False)
        if ret['msg']['opRet'] != '0':
            return False

        return True

    def do_bricks_exist_in_shd_volfile(self, volname: str,
                                       brick_list: list,
                                       node: str) -> bool:
        """
        Checks whether the given brick list is present in glustershd
        server volume file

        Args:
            volname (str): Name of the volume.
            brick_list (list): brick list of a volume which needs to
                               compare in glustershd server volume file
            node (str): Node on which commands will be executed.

        Returns:
            bool : True if brick exists in glustershd server volume file.
                   False Otherwise
        """
        GLUSTERSHD = "/var/lib/glusterd/glustershd/glustershd-server.vol"
        path = f"/var/lib/glusterd/vols/{volname}/{volname}-shd.vol"
        if not self.path_exists(node, GLUSTERSHD):
            if not self.path_exists(node, path):
                self.logger.error("Can't find shd file")
            else:
                GLUSTERSHD = path

        brick_list_server_vol = []
        volume_clients = f"volume {volname}-client-"
        host = brick = None
        parse = False

        cmd = f"cat {GLUSTERSHD}"
        ret = self.execute_abstract_op_node(cmd, node, False)

        if ret['error_code'] != 0:
            self.logger.error("Unable to cat the GLUSTERSHD file")
            return False

        fd = ''.join(ret['msg']).split('\n')
        for each_line in fd:
            each_line = each_line.strip()
            if volume_clients in each_line:
                parse = True
            elif "end-volume" in each_line:
                if parse:
                    brick_list_server_vol.append(f"{host}:{brick}")
                parse = False
            elif parse:
                if "option remote-subvolume" in each_line:
                    brick = each_line.split(" ")[2]
                if "option remote-host" in each_line:
                    host = each_line.split(" ")[2]

        self.logger.debug(f"Brick List from volume "
                          f"info: {brick_list}")
        self.logger.debug("Brick List from glustershd server volume "
                          f"file: {brick_list_server_vol}")

        if set(brick_list) != set(brick_list_server_vol):
            return False
        return True
