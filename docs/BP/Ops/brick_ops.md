# Brick Ops:

The code can be found at [brick_ops.py](../../../common/ops/gluster_ops/brick_ops.py)

1) **add_brick**<br>
		This method is used to add a brick or a set of bricks to the volume.

		Args:
			1. volname (str): The volume in which the brick has to be added.
			2. brick_str (list): String of brick cmd created by form_brick_cmd function.
			3. node (str): The node on which the command is to be run.
			4. force (bool): If set to True will add force in the command being executed.
			5. replica count (int): Optional parameter with default value of None.
			6. arbiter_count (int): Optional parameter with default value of None.
		Returns:
			A dictionary consisting                                        
            1. Flag : Flag to check if connection failed                 
            2. msg : message                                             
            3. error_msg: error message                                  
            4. error_code: error code returned                           
            5. cmd : command that got executed                           
            6. node : node on which the command got executed
		Example:
			self.add_brick(self.vol_name, brick_cmd, self.server_list[0],
                           replica_count=3)

2) **remove_brick**<br>
Remove brick does the opposite of add_brick operation and that is it removes existing brick or bricks from the volume. It has almost the same set of arguments apart from `option` which stores the remove brick options like start, commit, stop etc:

		Args:
			1. node (str): Node on which the command has to be executed.
			2. volname (str): The volume from which brick or a set of bricks have to be removed.
			3. brick_list (list): The list of bricks to be removed.
			4. option (str): Remove brick options: <start|stop|status|commit|force>
			5. replica_count (int): Optional argument with default value of None. This represent the desired replica count after the removal of the said bricks.
		Returns:
			A dictionary consisting                                        
            1. Flag : Flag to check if connection failed                 
            2. msg : message                                             
            3. error_msg: error message                                  
            4. error_code: error code returned                           
            5. cmd : command that got executed                           
            6. node : node on which the command got executed
		Example:
			self.remove_brick(self.server_list[0], self.vol_name, self.brick_list, option)

3) **replace_brick**<br>
		This function replaces one brick with another brick or in other words, source brick with destination brick. For now, the arguments it takes include:

		Args:
			1. node (str): The node on which the command has to be executed
			2. volname (str): The volume on which the bricks have to be replaced.
			3. src_brick (str) : The source brick name
			4. dest_brick (str) : The destination brick name
		Returns:
			A dictionary consisting                                        
            1. Flag : Flag to check if connection failed                 
            2. msg : message                                             
            3. error_msg: error message                                  
            4. error_code: error code returned                           
            5. cmd : command that got executed                           
            6. node : node on which the command got executed
		Example:
			self.replace_brick(self.server_list[0], self.vol_name, src_brick, dest_brick)

4) **reset-brick**<br>
		This function resets a brick in the volume. Reset-brick is useful in case a disk goes bad etc. It provides support to reformat the disk that the brick represents in the volume

		Args:
			1. node (str) : Node on which the command has to be executed
			2. volname (str) : Name of the volume on which the brick has to be reset
			3. src_brick (str) : Name of the source brick
			4. dst_brick (str) : Name of the destination brick
			5. option (str) : Options for reset brick : start | commit | force
		Returns:
			A dictionary consisting                                        
            1. Flag : Flag to check if connection failed                 
            2. msg : message                                             
            3. error_msg: error message                                  
            4. error_code: error code returned                           
            5. cmd : command that got executed                           
            6. node : node on which the command got executed
		Example:
			self.reset_brick(self.server_list[0], self.vol_name, src_brick, option, dest_brick)

5) **form_brick_cmd**<br>
		This function helps in creating the brick command from the brick paths. It requires the following arguments:

		Args:
			1. server_list (list): List of servers
			2. brick_root (list) : List of brick roots
			3. volname (str) : Name of the volume
			4. mul_fac (int) : Stores the number of bricks needed to form the brick command
			5. add_flag (bool): Optional parameter with default value of False. When set, the brick cmd creation will happen with respect to brick addition.
		Returns:
			A tuple containing
				1. brick_dict (dict) : Dictionary of server and their corresponding brick roots.
				2. brick_cmd (str) : Command which contains the brick paths.
		Example:
			self.form_brick_cmd(self.server_list, self.brick_root, self.vol_name, mul_factor, True)

6) **cleanup_brick_dirs**<br>
		Function for clearing out all the directory paths present in the cleands data structure.

		Args:
			None
		Returns:
			None
		Example:
			self.cleanup_brick_dirs()

7) **are_bricks_offline**<br>
		This function checks if the given list of bricks are offline.

		Args:
		    1. volname (str) : Volume name
    		2. bricks_list (list) : list of bricks to check
    		3. node (str) : the node on which comparison has to be done
    		4. strict (bool) : To check strictly if all bricks are offline or atleast one brick is offline.
		Returns:
    		boolean value: True, if bricks are offline else False
		Example:
			redant.are_bricks_offline(self.vol_name, bricks_list, self.server_list[0])

8) **check_if_bricks_list_changed**<br>
		Function checks if the bricks list changed. Basically, compares the bricks list with the bricks attained from volume info.

 		Args:
    		1. bricks_list (list): list of bricks
    		2. volname (str): Name of volume
    		3. node (str): Node on which to execute vol info

		Returns:
			bool: True if list is changed else False
		Example:
			redant.check_if_bricks_list_changed(bricks_list, self.vol_name, self.server_list[0])

9) **get_all_bricks**<br>
		Function to get the list of all the bricks of the specified volume.

		Args:
			1. volname (str): Name of the volume
			2. node (str): The node wherein the command is executed.
		Returns:
			List of all bricks else None on failure.
		Example:
			self.get_all_bricks(self.vol_name, self.server_list[0])

10) **get_online_bricks_list**<br>
		Function to get the list of all bricks which are online.

		Args:
			1. volname (str): Name of the volume
			2. node (str): Noe wherein the command is to be exexuted.
		Returns:
			List of bricks which are online in the format of server:brick_path on failure, if returns None
		Example:
			online_list = self.get_online_bricks_list(self.vol_name, self.server_list[2])

11) **get_offline_bricks_list**<br>
		Function to get the list of all bricks which are offline.

		Args:
			1. volname (str): Name of the volume
			2. node (str): Noe wherein the command is to be exexuted.
		Returns:
			List of bricks which are offline in the format of server:brick_path on failure, if returns None
		Example:
			offline_list = self.get_offline_bricks_list(self.vol_name, self.server_list[2])

12) **bring_bricks_offline**<br>
		Function to bring the given seet of bricks offline.

		Args:
			1. volname (str): Name of the volume to which these bricks belong to.
			2. brick_list (list): The list of bricks which are to be brought offline.
			3. timeout (int): optional parameter with default value as 100. The function waits for these many seconds for the bricks to go offline at max.
		Returns:
			True if bricks have been successfully brough offline else False.
		Example:
			self.bring_bricks_offline(self.volname, self.brick_list[2:4])

13) **bring_bricks_online**<br>
		Function to bring the given seet of bricks online.

		Args:
			1. volname (str): Name of the volume to which these bricks belong to.
			2. brick_list (list): The list of bricks which are to be brought online.
			3. timeout (int): optional parameter with default value as 100. The function waits for these many seconds for the bricks to come online at max.
		Returns:
			True if bricks have been successfully brough online else False.
		Example:
			self.bring_bricks_offline(self.volname, self.brick_list[2:4])

14) **wait_for_bricks_to_go_offline**<br>
		Function to wait till a given set of bricks go offline

		Args:
			1. volname (str): Name of the volume whose bricks are to be noticed.
			2. brick_list (list): The list of bricks which are expected to go offline.
			3. timeout (int): optional parameter with default value as 100. The function waits for these many seconds for the bricks to go offline at max.
		Returns:
			True if bricks have been successfully gone offline else False.
		Example:
			self.wait_for_bricks_to_go_offline(self.vol_name, self.brick_list, timeout)

15) **wait_for_bricks_to_come_online**<br>
		Function to wait till a given set of bricks come online

		Args:
			1. volname (str): Name of the volume whose bricks are to be noticed.
			2. server_list (str): The list of nodes wherein the volume is hosted.
			2. brick_list (list): The list of bricks which are expected to come online.
			3. timeout (int): optional parameter with default value as 100. The function waits for these many seconds for the bricks to come online at max.
		Returns:
			True if bricks have been successfully come online else False.
		Example:
			self.wait_for_bricks_to_come_online(self.volname, self.server_list, self.brick_list, timeout)

16) **replace_brick_from_volume**<br>
		Function to replace a faulty brick from a volume.

		Args:
            volname (str): Volume in which the brick has to be replaced
            node (str): Node on which command has to be executed
            server_list (list): List of servers in the cluster

        Optional:
            src_brick (str): Brick to be replaced
            dst_brick (str): New brick which will replace the old one
            delete_brick (bool): True, if the old brick should be deleted otherwise False. (Default is True)

        Returns:
            bool: True if the replace brick operation was successful,
                  False if the operation failed.
		
		Example:
			redant.replace_brick_from_volume(self.vol_name,
											 self.server_list[0],
											 self.server_list,
											 brick_to_replace,
											 new_brick_to_replace)

17) **are_bricks_online**<br>
		Function to check if the given list of bricks are online.

		Args:
            volname (str) : Volume name
            bricks_list (list) : list of bricks to check
            node (str) : the node on which comparison has to be done
            strict (bool) : To check strictly if all bricks are online
        Returns:
            boolean value: True, if bricks are online
                           False, if offline

		Example:
			redant.are_bricks_online(self.vol_name, bricks_list, self.server_list[0])

18) **get_brick_processes_count**<br>
		This function helps in getting the brick process count for a given node.

        Args:
            node (str): Node on which brick process has to be counted.

        Returns:
            int: Number of brick processes running on the node.
            None: If the command fails to execute.
        
		Example:
			count = redant.get_brick_processes_count(server)
