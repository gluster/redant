# IO Ops

[IO Ops](../../../common/ops/support/io_ops.py) contains all the functions which are required for the IO operations on the client and the servers.

## Given below are all the details about all the functions implemented in the IO ops module:

1) **create_file**<br>
        Function for a file creation

        Args:
            path (str): Path at which the file is to be created. This should be the absolue file path.
            filename (str): Name of the file to be created.
            nodes (str): Node wherein the file has to be created.
        Returns:
            True if file creation is successful or if the file already exists else False.
        Example:
            create_file(path, "sample_file", self.client_list[0])

2) **create_dir**<br>
        Function to create a directory.

        Args:
            path (str): path at which the directory has to be created. This should be the absolute path.
            dirname (str): The name of the directory.
            node (str): Node wherein the directory has to be created.
            excep (bool): An optional parameter. Determines whether to use the exception handling at abstract ops or not. Default value being True.
        Returns:
            The return dictionary provided by the abstract_ops.
        Example:
            ret = create_dir(path, dirname, self.client_list[0], False)

3) **path_exists**<br>
        Function to check whether a said paths exists on the said nodes.

        Args:
            list_of_nodes (list): A list of node on which the file has to be checked. One can also provide a single string representing one node.
            list_of_paths (list) : All the paths which have to be checked for existance. One can again provide a string of one path and the function will take care of it.
        Returns:
        	Boolean value. True if the paths exists on the nodes or False
		Example:
			ret = self.path_exists(self.server_list[0], ["/mnt", "/mnt/foo"])

4) **get_file_stat**<br>
        Function to get stat data for a file or directory.

        Args:
            node (str): The node on which we will perform the stat.
            path (str): The path on which stat will be performed.
        Returns:
        	Dictionary contianing following key value pair
            1. error_code : 0 for success and rest failure code.
            2. msg: A dictionary of stat data or a string containing the error statement.
		Example:
			ret = self.get_file_stat(self.client_list[0], "/mnt")

5) **create_deep_dirs_with_files**<br>
		Function to create deep directories and files under those directories in said node.

		Args:
			path (str): Absolute path over which this io has to be performed.
			dir_start_no (int): From which number, the directory numbering should be started.
			dir_depth (int): The depth till which dirs will be created.
			dir_length (int): The number of dirs at the top level.
			max_no_dirs (int): The number of dirs in a level.
			no_files (int): Number of files to be created under a directory.
			node (str): node wherein this has to be performed.
		Returns:
			async_object. For reference read the [rexe_ops](./rexe.md)
		Example:
			ret = self.create_deep_dirs_with_files("/mnt/foo", 1, 4, 5, 3, 12, self.client_list[0])

6) **get_file_permission**<br>
		Function to get the file permissions on a said node for a path.

		Args:
			node (str) : Node wherein the operation has to be performed.
			path (str) : The path for which permissions are required.
		Returns:
			Dictionary of the form,
				1. error_code: 0 for success, rest are standard failure error codes.
				2. file_perm : The file permission in integer form or 0 for failure.
