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
        return True

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
        status = self.check_power_node_status(node)
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
        status = self.check_power_node_status(node)
        if not status[node]:
            self.logger.info(f"{node} offline.")
            return True
        self.logger.error(f"{node} still online.")
        return False
