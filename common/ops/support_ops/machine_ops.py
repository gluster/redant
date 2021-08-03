"""
Machine ops is the swiss army knife of operational functions required
to perform server related configuration changes, be it network stack,
systemd changes or maybe a node reboot itself.
"""
import time
import os
import socket
from common.ops.abstract_ops import AbstractOps


class MachineOps(AbstractOps):
    """
    MachineOps class provides methods for
    handling the machine specific operations.
    """

    def reboot_nodes(self, nodes: list):
        """
        To reboot a given set of node(s)
        Arg:
            node(s) (str/list)
        """
        if not isinstance(nodes, list):
            nodes = [nodes]

        for node in nodes:
            self.reboot_node(node)
            self.wait_node_power_down(node)

    def check_node_power_status(self, nodes: list) -> dict:
        """
        To check the node's power status. Simply to check if
        it is online or offline.
        Arg:
            node(s) (str/list)
        Returns:
            dict containing following key-value pairs,
                -> node (str) : state (True/False)
            herein True implies node being online and False, offline.
        """
        if not isinstance(nodes, list):
            nodes = [nodes]

        ret = {}
        for node in nodes:
            cmd = (f"ping -c1 -W1 -q {node} &>/dev/null")
            ret_val = int(os.system(cmd))
            self.logger.info(f"Ping command {cmd} : {ret_val}")
            if ret_val != 0:
                ret[node] = False
            else:
                ret[node] = True
        self.logger.info(f"{nodes} power state : {ret}")
        return ret

    def are_nodes_online(self, nodes: str):
        """
        Checks if all the nodes are online.

        Args:
            nodes (str|list): List of nodes
        Return:
        True if all the nodes are online else False
        """
        ret = self.check_node_power_status(nodes)

        return all(list(ret.values()))

    def wait_node_power_up(self, node: str, timeout: int = 100):
        """
        Wait for a node to come up online.
        Arg:
            node (str)
        Returns:
            bool value: True if node is online or False.
        """
        iter_v = 0
        while iter_v < timeout:
            status = self.check_node_power_status(node)
            if status[node]:
                self.logger.info(f"{node} online.")
                return True
            time.sleep(1)
            iter_v += 1

        self.logger.error(f"{node} still offline.")
        return False

    def wait_node_power_down(self, node: str, timeout: int = 100):
        """
        Wait for a node to come down offline.
        Arg:
            node (str)
        Returns:
            bool value: True if node is offline or False.
        """
        iter_v = 0
        while iter_v < timeout:
            status = self.check_node_power_status(node)
            if not status[node]:
                self.logger.info(f"{node} offline.")
                return True
            time.sleep(1)
            iter_v += 1

        self.logger.error(f"{node} still online.")
        return False

    def hard_terminate(self, server_list: list, client_list: list,
                       brick_root: dict):
        """
        hard terminate is inconsiderate. It will clear out the env
        completely and is to be used with caution. Don't use it inside the
        non disruptive tests or else, you might have a string of failures.
        Args:
            server_list (list): List of gluster server machines
            client_list (list): List of gluster client machines
            brick_root (dict): Dictionary of brick roots and nodes.
        """
        # Wait for nodes to power up.
        for server in server_list:
            self.wait_node_power_up(server)

        # Stop glusterd on the servers.
        self.stop_glusterd(server_list)

        # Wait for glusterd to stop.
        if not self.wait_for_glusterd_to_stop(server_list):
            raise Exception("Sheer panic! As hard terminate fails to stop"
                            "glusterd!")

        # Kill glusterfs and glusterfsd processes in the server machines.
        # TODO. Add other gluster related processes later.
        cmd = "pkill glusterfs; pkill glusterfsd"
        for node in server_list:
            self.execute_abstract_op_node(cmd, node, False)

        # Also need to kill the fuse process in the clients
        cmd = "pkill glusterfs"
        for node in client_list:
            self.execute_abstract_op_node(cmd, node, False)

        # Clear out the content in vol, peer, snaps and glusterfind keys
        # directory on the servers.
        cmd = ("rm -rf /var/lib/glusterd/vols/*; rm -rf /var/lib/glusterd"
               "/peers/*; rm -rf /var/lib/glusterd/snaps/*; "
               "rm -rf /var/lib/glusterd/glusterfind/.keys/*")
        for node in server_list:
            self.execute_abstract_op_node(cmd, node, False)

        # Clear out the brick dirs under the brick roots.
        for (server, brick_list) in brick_root.items():
            for brick in brick_list:
                cmd = (f"rm -rf {brick}/*")
                self.execute_abstract_op_node(cmd, server, False)

        # Clear out the mountpoints in clients.
        cmd = "umount /mnt/*; rm -rf /mnt/*"
        for node in client_list:
            self.execute_abstract_op_node(cmd, node, False)

        # Unmount snap bricks.
        self.umount_snap_brick_from_servers(server_list)

        # Check for stray LVs and delete them.
        lv_dict = self.get_lv_paths_from_servers(server_list)

        self.remove_snap_lv(lv_dict)

        # Flush the IP tables
        cmd = "iptables --flush"
        for node in server_list:
            self.execute_abstract_op_node(cmd, node, False)

        self.es.reset_ds()

    def check_os(self, os_name: str, nodes: str,
                 os_version: str = None) -> bool:
        """
        Checks the os release and compares the os and version.

        Args:
            os_name (str): Operating system name.
            nodes (str|list): Nodes on which command has to be executed.
            os_version (str): Optional parameter with default value None.
                              Operating system version.

        Returns: bool, True, if os_name and os_version found
                 else False
        """
        cmd = "cat /etc/os-release"
        os_name = os_name.lower()

        ret = self.execute_abstract_op_multinode(cmd,
                                                 nodes,
                                                 False)
        for item in ret:
            if item['error_code'] != 0:
                self.logger.error("Couldn't fetch the os-release"
                                  f" from {item['node']}")
                return False

            out = item['msg']
            if os_version:
                if (
                    os_name not in out[0].lower()
                    or os_version not in out[1]
                ):
                    return False
            elif os_name not in out[0].lower():
                return False

        return True

    def bring_down_network_interface(self, node: str,
                                     timeout: int = 150):
        """Brings the network interface down for a defined time

            Args:
                node (str): Node at which the interface has to be bought down
                timeout (int): Time duration (in secs) for which network has to
                               be down

            Returns:
                network_status(object): Returns a process object
        """
        int_cmd = "ps -aux | grep glusterd"
        ret = self.execute_abstract_op_node(int_cmd,
                                            node, False)
        pid = None
        for i in ret['msg'][0].split(' '):
            if i.isnumeric():
                pid = i
                break

        int_cmd = f"cat /proc/{pid}/net/route"
        ret = self.execute_abstract_op_node(int_cmd,
                                            node, False)
        if ret['error_code'] != 0:
            raise Exception("Failed: Could not find the interface")

        interface = ret['msg'][1].split('\t')[0]

        cmd = (f"ip link set {interface} down\nsleep {timeout}\n"
               f"ip link set {interface} up")
        cmd1 = f"echo  \"{cmd}\"> 'test.sh'"
        self.execute_abstract_op_node(cmd1, node)
        network_status = self.execute_command_async("sh test.sh", node)
        return network_status

    def reload_glusterd_service(self, node: str) -> bool:
        """
        Reload the Daemons when unit files are changed.

        Args:
            node (str): Node on which daemon has to be reloaded.

        Returns:
            bool: True, On successful daemon reload
                False, Otherwise
        """
        if self.check_os('rhel', [node], '6'):
            cmd = 'service glusterd reload'
            ret = self.execute_abstract_op_node(node, cmd, False)
        else:
            cmd = "systemctl daemon-reload"
            ret = self.execute_abstract_op_node(cmd, node, False)

        if ret['error_code'] != 0:
            self.logger.error("Failed to reload the daemon")
            return False
        return True

    def convert_hosts_to_ip(self, node_list: list, node: str = None) -> list:
        """
        Redant framework works with IP addresses ( especially rexe )
        hence it makes sense to have a function to handle the conversion
        a node_list containing hostnames to ip addresses and if there's
        a localhost term, that is replaced by the node value.
        Args:
            node_list (list): List of nodes obtained wherein the node can
                              be represented by ip or hostname.
            node (str): The node which is represented by localhost. Has to
                        be replaced by corresponding IP.
        Returns:
            list : list of converted IPs
        """
        new_node_list = []

        if not isinstance(node_list, list):
            node_list = [node_list]

        # Replace localhost with its hostname
        if 'localhost' in node_list:
            new_node_list.append(node)
            node_list.remove('localhost')

        for value in node_list:
            if not value.replace('.', '').isnumeric():
                ip_val = socket.gethostbyname(value)
                new_node_list.append(ip_val)
            else:
                new_node_list.append(value)

        return new_node_list

    def get_lv_paths_from_servers(self, nodes: list) -> list:
        """
        Method to obtain the LV Paths in the machine.

        Args:
            node (str|list): Node whose LV path detail is required.

        Returns:
            List of paths.
        """
        cmd = "lvs --noheadings -o lv_path | awk '{if ($1) print $1}'"
        lv_paths = {}

        if not isinstance(nodes, list):
            nodes = [nodes]

        for node in nodes:
            ret = self.execute_abstract_op_node(cmd, node)
            server_path = [path.strip() for path in ret['msg']]
            lv_paths[node] = server_path
        return lv_paths

    def remove_lv_paths_from_servers(self, lv_dict: dict):
        """
        Method to remove LV paths.

        Args:
            lv_dict (dict): It is a dictionary wherein the key is the node
            and the value being the list of LVs corresponding to that node.
        """
        for node in lv_dict:
            for lv_path in lv_dict[node]:
                cmd = (f"lvremove {lv_path} --force")
                self.execute_abstract_op_node(cmd, node)

    def remove_snap_lv(self, lv_dict: dict):
        """
        Method to find out the gluster snap specific lv and then remove it.

        Args:
            lv_dict (dict): It is a dictionary wherein the key is the node
            and the value being the list of LV paths corresponding to that
            node.
        """
        snap_lv_dict = {}

        for node in lv_dict:
            snap_lv_dict[node] = []
            for lv_path in lv_dict[node]:
                split_lv_path = lv_path.split('/')[-1].split('_')
                if len(split_lv_path) == 2 and len(split_lv_path[0]) == 32 and\
                        split_lv_path[1].isalnum():
                    snap_lv_dict[node].append(lv_path)
            if snap_lv_dict[node] == []:
                del snap_lv_dict[node]

        self.remove_lv_paths_from_servers(snap_lv_dict)
