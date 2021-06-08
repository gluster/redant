# Glusterd Ops

[Glusterd Ops](../../../common/ops/gluster_ops/gluster_ops.py) contains all the functions which are required for glusterd specific operations.

## Given below are all the details about all the functions implemented in the Glusterd Ops module:

1) **start_glusterd**<br>
        Function to start glusterd

        Args:
            nodes (list): Nodes on which glusterd is to be started.
            enable_retry (bool): Optional parameter with default value as True.
                                 If enabled, it'll bypass the burst limit of
                                 glusterd.
        Returns:
            dictionary of the following form
            	1. Flag: Flag to check if the connection failed.
				2. msg: stdout message
				3. error_msg: stderr message
				4. error_code: error code returned
				5. cmd: Command that got executed
				6. node: node on which the command is run
        Example:
            self.start_glusterd(self.server_list[0])

2) **restart_glusterd**<br>
		Function to restart glusterd.

        Args:
            nodes (list): List of nodes no which glusterd is to be restarted.
            enable_retry (bool): Optional parameter with default value as True.
                                 If enabled, it'll bypass the burst limit of
                                 glusterd.
        Returns:
            dictionary of the following form
            	1. Flag: Flag to check if the connection failed.
				2. msg: stdout message
				3. error_msg: stderr message
				4. error_code: error code returned
				5. cmd: Command that got executed
				6. node: node on which the command is run
        Example:
            self.restart_glusterd(self.server_list[0])

3) **stop_glusterd**<br>
        Function to stop glusterd

        Args:
            node (list): The nodes on which glusterd has to be stopped.
        Returns:
            dictionary of the following form
            	1. Flag: Flag to check if the connection failed.
				2. msg: stdout message
				3. error_msg: stderr message
				4. error_code: error code returned
				5. cmd: Command that got executed
				6. node: node on which the command is run
        Example:
            self.stop_glusterd(self.server_list[0])

4) **reset_failed_glusterd**<br>
        Function to reset the start burst limit for glusterd.

        Args:
            node (list): Nodes on which the burst limit is to be reset.
        Returns:
            dictionary of the following form
            	1. Flag: Flag to check if the connection failed.
				2. msg: stdout message
				3. error_msg: stderr message
				4. error_code: error code returned
				5. cmd: Command that got executed
				6. node: node on which the command is run
        Example:
            self.reset_failed_glusterd(self.server_list[0])

5) **is_glusterd_running**<br>
        Function to check ig glusterd is running in the said servers.

        Args:
            node (list): Nodes on which the glusterd state has to be checked.
        Returns:
			1: if glusterd is active on said servers
			0: if glusterd is not active on said servers
			-1: if glusterd is not active but PID is alive in said servers.
		Example:
			self.is_glusterd_running(self.server_list)

6) **wait_for_glusterd_to_start**<br>
		Function to wait for glusterd to start on said node.

		Args:
			1. node (str): The node on which the state is to be checked.
			2. timeout (int): Optional parameter with default value as 80. This
                              is the max time till which the function will wait
                              for glusterd to start on the said server.
		Returns:
			True is the state is started else False
		Example:
			self.wait_for_glusterd_to_start(self.server_list[0])

7) **wait_for_glusterd_to_stop**<br>
		Function to wait for glusterd to stop on said node.

		Args:
			1. node (str): The node on which the state is to be checked.
			2. timeout (int): Optional parameter with default value as 80. This
                              is the max time till which the function will wait
                              for glusterd to stop on the said server.
		Returns:
			True is the state is stopped else False
		Example:
			self.wait_for_glusterd_to_stop(self.server_list[0])

8) **get_state**<br>
		Function to run gluster get-state command on a said node.

		Args:
			1. node (str): Node on which the command is to be run.
		Returns:
			The get-state output in dictionary format on success
		Example:
			self.get_state(self.server_list[0])

9) **get_gluster_version**<br>
		This function checks the glusterfs version on the node.

        Args:
            node (str): Node wherein the gluster version is
                        checked.

        Returns:
            str: The gluster version value.

		Example:
			ver = redant.get_gluster_version(self.server_list[0])

	
10) **get_glusterd_process_count**<br>
	This function gets the gluster process count for a given node.

        Args:
            node (str): Node on which glusterd process has to be counted.

        Returns:
            int: Number of glusterd processes running on the node.
            None: If the command fails to execute.

		Example:
			pcnt = redant.get_glusterd_process_count(self.server_list[0])


11) **get_all_gluster_process_coun**<br>
		This function gets all gluster related process count for a given node.

        Args:
            node (str): Node on which gluster process has to be counted.

        Returns:
            int: Number of gluster processes running on the node.
            None: If the command fails to execute.

		Example:
			pcnt = redant.get_all_gluster_process_count(self.server_list[0])