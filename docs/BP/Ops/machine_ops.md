# Machine Ops

[Machine Ops](../../../common/ops/support/machine_ops.py) contains all the functions which are required for machine level operations such as firewall rules, node power state etc.

## Given below are all the details about all the functions implemented in the Machine Ops module:

1) **reboot_nodes**<br>
        To reboot a given a set of node(s)

        Args:
            nodes (list): List of nodes which are to be rebooted. Can also be provided as a string.
        Returns:
            None
        Example:
            reboot_nodes(self.server_list[0])

2) **check_node_power_status**<br>
        To check the node's power status. To simply check if it online or offline.

        Args:
            nodes (list): List of nodes whose status is to be checked.
        Returns:
            A dictionary of the form,
            {
                "node1" : True/False,
                "node2" : True/False,
                ...
                "noden" : True/False
            }
        Example:
            ret = check_node_power_status(self.server_list)

3) **wait_node_power_up**<br>
        Wait for the said node to come up.

        Args:
            node (str): The node for which we have to wait till it comes up oneline.
            timeout (int): Default value 100. We will wait for x seconds till the node comes up.
        Returns:
        	Boolean value. True if the node comes up within timeout or else False.
		Example:
			ret = self.wait_for_node_power_up(self.server_list[0])

4) **wait_node_power_down**<br>
        Wait for the said node to go down.

        Args:
            node (str): The node for which we have to wait till it goes down.
            timeout (int): Default value 100. We will wait for x seconds till the node comes goes down.
        Returns:
        	Boolean value. True if the node goes down within timeout or else False.
		Example:
			ret = self.wait_for_node_power_down(self.server_list[0])
