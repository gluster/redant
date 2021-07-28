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

5) **hard_terminate**<br>

        This function will clear out the env completely and is to be used with caution. Don't use it inside the non disruptive tests or else, you might have a string of failures.

        Args:
            server_list (list): List of gluster server machines
            client_list (list): List of gluster client machines
            brick_root (dict): Dictionary of brick roots and nodes.

        Example:
            self.redant.hard_terminate(self.server_list, self.client_list,
                                       self.brick_root)

6) **isrhel7**<br>

        Function to check whether the machine or list of machines are rhel-7.

        Args:
        servers (str|list): A server|List of servers hosts to
                            know the RHEL Version

        Returns:
        bool:Returns True, if its RHEL-7 else returns false
        
        Example:
            self.is_rhel7(self.server_list)

7) **bring_down_network_interface**<br>

        This function brings the network interface down for a defined time

            Args:
                node (str): Node at which the interface has to be bought down
                timeout (int): Time duration (in secs) for which network has to be down

            Returns:
                network_status(object): Returns a process object

            Example:
                self.bring_down_network_interface(self.server_list[0])
        
