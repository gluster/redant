# Snapshot Ops

[Snapshot Ops](../../../common/ops/gluster_ops/snapshot_ops.py) contains all the functions required to carry out the snapshot related ops.

1) **enable_uss**<br>
		Enables uss option.

		Args:
			volname (str): volume name
			node (str): Node on which cmd has to be executed.
			excep (bool): Optional parameter with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
		
		Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
                
        Example:
        ```python
            redant.enable_uss(self.vol_name, self.server_list[0])
		```

2) **disable_uss**<br>
		Disables uss option.
		
		Args:
			volname (str): volume name
			node (str): Node on which cmd has to be executed.
			excep (bool): Optional parameter with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
		
		Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
                
        Example:
        ```python
            redant.disable_uss(self.vol_name, self.server_list[0])
		```

3) **is_uss_enabled**<br>
		Checks if the uss is enabled.
		
		Args:
			volname (str): volume name
			node (str): Node wherein the command is executed.
		
		Returns:
			bool: True if enabled or else False.
			
		Example:
		```python
			ret = redant.is_uss_enabled(self.vol_name, self.server_list[0])
		```

4) **is_uss_disabled**<br>
		Checks if the uss is disabled.
		
		Args:
			volname (str): volume name
			node (str): Node wherein the command is executed.
		
		Returns:
			bool: True if disabled or else False.
			
		Example:
		```python
			ret = redant.is_uss_disabled(self.vol_name, self.server_list[0])
		```

5) **is_snapd_running**<br>
		Checks whether snapd is running or not.
		
		Args:
			volname (str): volume name
			node (str): Node on which the command is run.
		
		Returns:
			bool: True if snapd is running or else False.

		Example:
		```python
			ret = redant.is_snapd_running(self.vol_name, self.server_list[0])
		```

6) **snap_create**<br>
		To create snapshot.
		
		Args:
			volname (str): Name of the volume for which snap is to be created.
			snapname (str): Name of the snapshot.
			node (str): Node wherein this command is to be run.
			timestamp (bool): Optional parameter, by default False. Determines whether the snap name should contain the timestamp or not.
			description (str): Optional parameter, by default None. If provided, it'll form as the description to be used during snap creation.
			force (bool): Optional parameter, by default False, Determines whether the snapshot should be created with force option or not.
			excep (bool): Optional parameter with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
		
		Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
                
        Example:
        ```python
            redant.snap_create(self.vol_name, self.snap_name, self.server_list[0], description="Sample snapshot")
		```

7) **snap_clone**<br>
		To clone a snapshot.
		
		Args:
			snapname (str): Name of the snapshot
			clonename (str): Name of the clone.
			node (str): Node wherein the command is to be run.
			excep (bool): Optional parameter with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
		
		Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
                
        Example:
        ```python
            redant.snap_clone(self.snap_name, self.clone_name, self.server_list[0])
		```

8) **snap_restore**<br>
		To restore a snapshot
		
		Args:
			snapname (str): name of the snapshot
			node (str): Node wherein the command is to be run.
			excep bool): Optional parameter with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
		
		Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
                
        Example:
        ```python
            redant.snap_restore(self.snap_name, self.server_list[0])
		```

9) **snap_restore_complete**<br>
		Stop a volume, restore the snapshot and restart the volume.
		
		Args:
			volname (str): Name of the volume
			snapname (str): Name of the snapshot
			node (str): Node wherein the command is run.
			excep (bool): Optional parameter with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
		
		Returns:
			bool: True if the whole operation is a success. Else False is returned.

		Example:
		```python
			redant.snap_restore_complete(self.vol_name, self.snap_name, self.server_list[0])
		```

10) **snap_status**<br>
		To obtain the snapshot status. One can either provide the volname or the snapname. If both are provided then snapname is used. Also, even though both parameters are optional, one has to provide either one of them.
		
		Args:
			node (str): Node wherein the command is run.
			snapname (str): Optional parameter with default value being None.
			volname (str): optional parameter with default value being None.
			excep bool): Optional parameter with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
		
		Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
                
        Example:
        ```python
            redant.snap_status(self.server_list[0], snapname=self.snap_name)
		```

11) **get_snap_status**<br>
		To get the snap status. The difference between this and the snap_status is that using this method, one gets a parsed output.
		
		Args:
			node (str): node wherein the command is run.
			excep bool): Optional parameter with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
		
		Returns:
			Dictionary of snapshot status in parsed mode. If excep is true, the parsing is done else, bypased and raw dictionary is returned.
		
		Example:
		```python
			redant.get_snap_status(self.server_list[0])
		```

12) **get_snap_status_by_snapname**<br>
		To get the snap status specific to the mentioned snapname.
		
		Args:
			node (str): Node wherein the command is run.
			excep bool): Optional argument with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
			
		Returns:
			Dictionary of snapshot status for said snapshot or NoneType.
		
		Example:
		```python
			redant.get_snap_status_by_snapname(self.snap_name, self.server_list[0])
		```

13) **snap_info**<br>
		To get the snapshot info.
		
		Args:
			node (str): Node wherein the command is run.
			snapname (str): Optional parameter, default value being None. Name of the snapshot
			volname (str): Optional parameter, default value being None. Name of the volume.
			excep (bool): Optional parameter with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
		
		Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
                
        Example:
        ```python
            redant.snap_info(self.server_list[0], snapname=self.snap_name)
		```

14) **get_snap_info**<br>
		To obtain the snap info command output when run in a node and to access the results by snapname.
		
		Args:
			node (str); Node wherein the command is run
			excep (bool): Optional parameter with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
		
		Returns:
			a dictionary in case of valid data or else NoneType.
		
		Example:
		```python
			redant.get_snap_info(self.server_list[0])
		```

15) **get_snap_info_by_snapname**<br>
		To obtain the snap info specific to a snapname.
		
		Args:
			snapname (str): Name of the snap whose info is to be obtained.
			node (str): Node wherein the command has to be run.

		Returns:
			Dictionary of snap info pertaining to a snapname and Nonetype object if not found.
		
		Example:
		```
			redant.get_snap_info_by_snapname(self.snap_name, self.server_list[0])
		```


16) **get_snap_info_by_volname**<br>
		To obtain the snap info specific to a volname.
		
		Args:
			volname (str): Name of the volume whose snap infos are to be obtained.
			node (str): Node wherein the command has to be run.

		Returns:
			Dictionary of snap infos pertaining to a volume and Nonetype object if not found.
		
		Example:
		```
			redant.get_snap_info_by_volname(self.vol_name, self.server_list[0])
		```

17) **snap_list**<br>
		To run snap list command and get the ret dict back.
		
		Args:
			node (str): Node wherein the command is run.
			excep (bool): Optional parameter with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
		
		Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
                
        Example:
        ```python
            redant.snap_list(self.server_list[0])
        ```

18) **get_snap_list**
		To obtain the snapshot list.
		
		Args:
			node (str): Node wherein the command is run.
			volname (str): Optional parameter with default value being None. When provided, the snap list is specific to the volname provided.
			excep (bool): Optional parameter with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
		
		Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
                when excep is False or else a list of snapshots is returned.
                
        Example:
        ```python
            redant.get_snap_list(self.server_list[0], self.vol_name)
        ```

19) **snap_delete**<br>
		To delete a specific snapshot.
		
		Args:
			snapname (str): Name of the snapshot which is to be deleted.
			node (str): Node wherein the command is run.
			excep (bool): Optional parameter with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
		
		Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
                
        Example:
        ```python
            redant.snap_delete(self.snap_name, self.server_list[0])
        ```

20) **snap_delete_by_volumename**<br>
		Delete a snapshot by volume name.
		
		Args:
			volname (str): Name of the volume whose snapshots are to be purged.
			node (str): Node wherein the command is to be executed.
			excep (bool): Optional parameter with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
		
		Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
                
        Example:
        ```python
            redant.snap_delete_by_volumename(self.vol_name, self.server_list[0])
        ```

21) **snap_delete_all**<br>
		Delete all snapshots present in the cluster.
		
		Args:
			node (str): Node wherien the command is to be run. This node is part of the cluster whose snaps are deleted.
			excep (bool): Optional parameter with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
		
		Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
                
        Example:
        ```python
            redant.snap_delete_all(self.server_list[0])
        ```

22) **snap_activate**<br>
		Activate a snapshot.
		
		Args:
			snapname (str): name of the snapshot to be activated.
			node (str): Node wherein the command is to be run.
			force (bool): Optional parameter with default value being False.
			excep (bool): Optional parameter with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
		
		Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
                
        Example:
        ```python
            redant.snap_activate(self.snap_name, self.server_list[0])
        ```

23) **snap_deactivate**<br>
		Deactivate a snapshot.
		
		Args:
			snapname (str): name of the snapshot to be de-activated.
			node (str): node wherein the command is to be run.
			excep (bool): Optional parameter with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
			
			Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
                
        Example:
        ```python
            redant.snap_deactivate(self.snap_name, self.server_list[0])
        ```

24) **terminate_snapds_on_node**<br>
		To stop snap process on the specified node.
		
		Args:
			node (str): Node wherien the command is to be run.
		
		Example:
		```
			redant.terminate_snapds_on_node(self.server_list[0])
		```

25) **get_snap_config**<br>
		To obtain the snap config
		
		Args:
			node (str): The node wherein the command is run.
			volname (str): Optional parameter with default value being None. When providede the config is parsed only for snaps derived from this volume.
			excep (bool): Optional parameter with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
			
			Returns:
				A dictionary of config values. Parsing would be done only when excep if True, else the raw output is returned to the user which is of the form,
				ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
            
            Example:
            ```
                redant.get_snap_config(self.server_list[0])
            ```

26) **set_snap_config**<br>
		To set the snap config.
		
		Args:
			option (dict): Key value pair of the option to be set.
			node (str): Node wherein the command is to be run.
			volname (str): Optional parameter with defauly value being None.
			excep (bool): Optional parameter with default value being True. With this true, the exception handling on the command execution will be handled by the framework.
			
			Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
                
        Example:
        ```python
            redant.set_snap_config(options_dict, self.server_list[0])
        ```
