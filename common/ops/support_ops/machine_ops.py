"""
Machine ops is the swiss army knife of operational functions required
to perform server related configuration changes, be it network stack,
systemd changes or maybe a node reboot itself.
"""
import time
import os
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
        Returns:
            None
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

    def wait_node_power_up(self, node: str, timeout: int = 100):
        """
        Wait for a node to come up online.
        Arg:
            node (str)
        Returns:
            bool value: True if node is online or False.
        """
        status = self.check_node_power_status(node)
        if status[node]:
            self.logger.info(f"{node} online.")
            return True
        iter_v = 0
        while iter_v < timeout:
            status = self.check_node_power_status(node)
            if status[node]:
                self.logger.info(f"{node} online.")
                return True
            time.sleep(1)
            iter_v += 1
        status = self.check_node_power_status(node)
        if status[node]:
            self.logger.info(f"{node} online.")
            return True
        self.logger.error(f"{node} still offline.")
        return False

    def wait_node_power_down(self, node: str, timeout: int = 100):
        """
        Wait for a node to come down offline.
        Arg:
            node (str)
        Returns:
            bool value: True if node is online or False.
        """
        status = self.check_node_power_status(node)
        if not status[node]:
            self.logger.info(f"{node} offline.")
            return True
        iter_v = 0
        while iter_v < timeout:
            status = self.check_node_power_status(node)
            if not status[node]:
                self.logger.info(f"{node} offline.")
                return True
            time.sleep(1)
            iter_v += 1
        status = self.check_node_power_status(node)
        if not status[node]:
            self.logger.info(f"{node} offline.")
            return True
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
        cmd = "pkill glusterfs && pkill glusterfsd"
        for node in server_list:
            self.execute_abstract_op_node(cmd, node, False)

        # Also need to kill the fuse process in the clients
        cmd = "pkill glusterfs"
        for node in client_list:
            self.execute_abstract_op_node(cmd, node, False)

        # Clear out the vol and peer file on the servers.
        cmd = ("rm -rf /var/lib/glusterd/vols/* && rm -rf /var/lib/glusterd"
               "/peers/*")
        for node in server_list:
            self.execute_abstract_op_node(cmd, node, False)

        # Clear out the brick dirs under the brick roots.
        for (server, brick) in brick_root.items():
            cmd = (f"rm -rf {brick}/*")
            self.execute_abstract_op_node(cmd, server, False)

        # Clear out the mountpoints in clients.
        cmd = "umount /mnt/* && rm -rf /mnt/*"
        for node in client_list:
            self.execute_abstract_op_node(cmd, node, False)

        # Flush the IP tables
        cmd = "iptables --flush"
        for node in server_list:
            self.execute_abstract_op_node(cmd, node, False)

    def is_rhel7(self, servers):
        """Function to get whether the server is RHEL-7

        Args:
        servers (str|list): A server|List of servers hosts to
                            know the RHEL Version

        Returns:
        bool:Returns True, if its RHEL-7 else returns false
        """
        if not isinstance(servers, list):
            servers = [servers]
        cmd = "cat /etc/redhat-release"
        results = self.execute_abstract_op_multinode(cmd,
                                                     servers)
        rc = True

        for item in results:
            if item['error_code'] != 0:
                self.logger.error(f"Unable to get RHEL version on"
                                  f"{item['node']}")
                rc = False
            if item['error_code'] == 0 and 'release 7' not in item['msg'][0]:
                self.logger.error(f"Server {item['node']} is not RHEL-7")
                rc = False
        return rc

    def bring_down_network_interface(self, node: str,
                                     timeout: int = 150):
        """Brings the network interface down for a defined time

            Args:
                node (str): Node at which the interface has to be bought down
                timeout (int): Time duration (in secs) for which network has to
                               be down

            Returns:
                network_status(object): Returns a process object

            Example:
                >>> bring_down_network_interface("10.70.43.68", timout=100)
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
