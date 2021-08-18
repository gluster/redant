# Environ Methods:

The code can be found at [environ.py](../../core/environ.py). This documentation contains the references
to the Framework Environ methods.

Before moving on to methods, let's take a look at the data structures.

1. volds ( volume data strucutre )
	```js
	{
		"volname1": {
						"started": False,
						"options": {
										"optionName1" : "optionValue1",
										...
								   },
						"mountpath": {
										"node1" : [ "mnt1", "mnt2" ... ],
										...
									 },
						"brickdata" : {
										"node1" : ["brick_path1", "brick_path2", ... ],
										...
									  },
						"voltype": {
										"dist_count" : 0,
										"replica_count" : 0,
										"disperse_count" : 0,
										"arbiter_count" : 0,
										"redundancy_count" : 0,
										"transport" : ""
									}
					},
					...
	}
	```
	
1) **init_ds**<br>
		To handle the creation of data structures to store the current state of the environment to run the framework.
		
		Example:
		```python
			redant.es.init_ds()
		```

2) **_validate_volname**<br>
		A helper method to validate incoming volname parameter is valid or not. Exception is raised if volname is not present.
		
		Args:
			volname (str): Name of the volume.
		
		Example:
		```python
			redant.es._validate_volname(self.vol_name)
		```

3) **set_new_volume**<br>
		Adding the volds components for a new volume.
		
		Args:
			volname (str): Name of the volume.
			brickdata (dict): Dictionary containing objects with key as node IPs and values being list of bricks lying under that said node.
		
		Example:
		```python
			redant.es.set_new_volume(self.vol_name, brick_data)
		```

4) **reset_ds**<br>
		To reset the data structures back to an empty dictionary.
		
		Example:
		```python
			redant.es.reset_ds()
		```

5) **get_volnames**<br>
		To obtain the list of volumes present in the volume data structure.
		
		Example:
		```python
			redant.es.get_volumes()
		```

6) **does_volume_exists**<br>
		To check if the said volume already exists in the volds.
		
		Args:
			volname (str): Name of the volume.
			
		Returns:
			Bool value, True if volume exists or else False.
		
		Example:
		```python
			redant.es.does_volume_exists(self.vol_name)
		```

7) **remove_volume_data**<br>
		Removing a volume's data from volds.
		
		Args:
			volname (str): name of the volume.
		
		Example:
		```python
			redant.es.remove_volume_data(self.vol_name)
		```

8) **get_volume_dict**<br>
		Get the volume dictionary for requested volume.
		
		Args:
			volname (str): Name fo the volume.
		
		Returns:
			Volds specific to a volume if volume is present or else exception is thrown.
		
		Example:
		```python
			redant.es.get_volume_dict(self.vol_name)
		```

9) **get_volds**<br>
		Returning back the volds.
		
		Returns:
			volds dictionary.
		
		Example:
		```python
			redant.es.get_volds()
		```

10) **set_vol_type**<br>
		Modifies the volds voltype based on voltype_dict
		
		Args:
			volname (str): Name of the volume.
			voltype_dict (dict): A dictionary wherein the key is the voltype parameter name and value being the count.
		
		Example:
		```python
			redant.es.set_vol_type(self.vol_name, self.voltype_dict)
		```

11) **set_vol_type_param**<br>
		Modifies the volds key for a specific volume by incoming delta_value for the said volume.
		
		Args:
			volname (str): Name of the volume for which the voltype params have to be modified.
			voltype_key (str): The volume parameter.
			delta_value (int): The integer value which is added to the existing value for the said voltype_key.
		
		Example:
		```python
			redant.es.set_vol_type_param(self.vol_name, self.voltype_key, delta_value)
		```

12) **get_vol_type_param**<br>
		Obtains the value corresponding to the said volume and the voltype_key.
		
		Args:
			volname (str): Name of the volume.
			voltype_key (str): Name of the voltype.
			
		Returns:
			The value corresponding to the voltype_key and None if it doesn't exist.
			
		Example:
		```python
			redant.es.get_vol_type_param(self.vol_name, self.voltype_key)
		```

13) **get_vol_type_changes**<br>
		Function to identify if there are any changes to the volumt type dictionary. More of an experimental function. Not yet completely formulated.
		
		Args:
			volname (str): Name of the volume.
			pre_voltype (dict): A volume type dictionary against which the current voltype dict of the said volname is compared.
			
		Returns:
			Bool value. True if there are any changes, else False.
			
		Example:
		```python
			redant.es.get_vol_type_changes(self.vol_name, pre_voltype)
		```

14) **add_new_mountpath**<br>
		To add a new mountpath for given volume and client node.
		
		Args
			volname (str): Name of the volume.
			node (str): Node wherein the volume is mounted.
			path (str): The absolute path of the mountpoint.
			
		Example:
		```python
			redant.es.add_new_mountpath(self.vol_name, self.client_list[0], mountpoint)
		```

15) **remove_mountpath**<br>
		Removes the mountpath entries under a client node for a given volume.
		
		Args:
			volname (str): Name of the volume.
			node (str): The client node.
			path (str): The path which is to be removed.
		
		Example:
		```python
			redant.es.remove_mountpath(self.vol_name, self.client_list[0], mountpoint)
		```
			
16) **get_mnt_pts_dict**<br>
		Method to obtain mountpath dictionary for a given volume.
		
		Args:
			volname (str): Name of the volume.
		
		Returns:
			Dicitonary of nodes and their list of mountpaths.
		
		Example:
		```python
			redant.es.get_mnt_pts_dict(self.vol_name)
		```
			
17) **get_mnt_pts_dict_in_list**<br>
		To obtain a modified list of mountpath which contains multiple client->mountpath relation.
		
		Args:
			volname (str): Name of the volume.
		
		Returns:.
			List of client->mountpath dictionaries.
		
		Example:
		```python
			redant.es.get_mnt_pts_dict_in_list(self.vol_name)
		```

18) **get_mnt_pts_list**<br>
		To obtain list of mountpath.
		
		Args:
			volname (str): Name of the volume.
			node (str): Optional parameter with default value None, The client node.
			
		Returns:
			List of mountpaths belonging to a node or list of all mountpoints when node isn't provided.
		
		Example:
		```python
			redant.es.get_mnt_pts_list(self.vol_name)
		```

19)**add_bricks_to_brickdata**<br>
		To add a new set of bricks into the existing brick data of a volume.
		
		Args:
			volname (str): Name of the volume.
			brick_dict (dict): A dictionary of keys with node ip and values being list of bricks under that node.
			
		Example:
		```python
			redant.es.add_bricks_to_brickdata(self.vol_name, brick_dict)
		```
			
20) **set_brickdata**<br>
		To replace the existing brickdata of a volume with whatever has been provided.
		
		Args:
			volname (str): Name of the volume
			brick_data (dict): A dictionary with keys of node ip and values being list of bricks under that node.
			
		Example:
		```python
			redant.set_brickdata(self.vol_name, brick_data)
		```

21) **remove_bricks_from_brickdata**<br>
		To remove the brick brickdata.
		
		Args:
			volname (str): Name of the volume.
			brick_data (dict): A dictionary with keys of node ip and values being list of bricks under that node.
			
		Example:
		```python
			redant.es.remove_bricks_from_brickdata(self.vol_name, brick_data)
		```

22) **get_brickdata**<br>
		To obtain the brick dictionary of a certain volume.
		
		Args:
			volname (str): name of the volume.
		
		Returns:
			Dictionary of keys of node ip and values being list of bricks under that node.

		Example:
		```python
			redant.es.get_brickdata(self.vol_name)
		```

23) **get_all_bricks_list**<br>
		To create a list of node->brick list for a given volume.
		
		Args:
			volname (str): Name of the volume.
		
		Returns:
			List of node:brick values.
			
		Example:
		```python
			redant.es.get_all_bricks_list(self.vol_name)
		```

24) **get_brick_list**<br>
		Method to obtain the list of bricks for a given volume and node.
		
		Args:
			volname (str): Name of the volume
			node (str): Node for which the brick data is required.
			
		Returns:
			list of bricks for the given node.
		
		Example:
		```python
			redant.es.get_brick_list(self.vol_name, self.server_list[1])
		```

25) **set_volume_start_status**<br>
		To set the volume start status of a given volume to True or False.
		
		Args:
			volname (str): Name of the volume.
			state (bool): The state can be True or False.
		
		Example:
		```python
			redant.es.set_volume_start_status(self.vol_name, state)
		```
		
26) **get_volume_start_status**<br>
		To get the volume start status of the volume mentioned.
		
		Args:
			volname (str): Name of the volume.
		
		Returns:
			bool value representing the status of the volume.
		
		Example:
		```python
			redant.es.get_volume_start_status(self.vol_name)
		```
			
27) **set_vol_option**<br>
		To set a volume option for said volume based on the dictionary of options provided.
		
		Args:
			volname (str): Name of the volume.
			options_dict (dict): Dictionary wherein key values are the options and the values being the option's values.
		
		Example:
		```python
			redant.es.set_vol_option(self.vol_name, options_dict)
		```

28) **set_vol_options_all**<br>
		To set options in the clusteropt dict.
		
		Args:
			option_dict (dict): Dictionary of cluster options and their corresponding values.

		Example:
		```python
			redant.es.set_vol_options_all(options_dict)
		```

29) **reset_vol_options_all**<br>
		To delete the clusteropts based on the option_list provided.
		
		Args:
			option_list (list): List of options which have to be removed from the clusteropts.
		
		Example:
		```python
			redant.reset_vol_options_all(option_list)
		```

30) **get_vol_options**<br>
		To obtain the volume options changed during the test case run.
		
		Args:
			volname (str): Name of the volume.
			
		Returns:
			Dictionary of options for a given volume.
		
		Example:
		```python
			redant.es.get_vol_options(self.vol_name)
		```

31) **get_vol_options_all**<br>
		To return the cluster options dictionary.
		
		Returns:
			Dictionary of cluster options.

		Example:
		```python
			redant.es.get_vol_options_all()
		```

32) **is_volume_options_populated**<br>
		To check whether the volume options of a given volume is populated or empty.
		
		Args:
			volname (str): Name of the volume.
		
		Returns:
			bool value. True if populated or else False.
		
		Example:
		```python
			redant.es.is_volume_options_populated(self.vol_name)
		```

33) **_reset_all_options_in_a_vol**<br>
		To reset all options of a given volume.
		
		Args:
			volname (str): Reset the volume options under a volume.

		Example:
		```python
			redant.es._reset_all_options_in_a_vol(self.vol_name)
		```

34) **reset_volume_option**<br>
		To reset the options of volumes based of volume name and the option provided.
		
		Args:
			volname (str): Name of the volume
			option (str): The option name.
		
		Example:
		```python
			redant.es.reset_volume_option(self.vol_name, option)
		```

35) **get_volume_nodes**<br>
		To get all the nodes whose bricks are part of a volume.
		
		Args:
			volname (str): Name fo the volume.
		
		Returns:
			List of nodes whose bricks are parts of the volume.
			
		Example:
		```python
			redant.es.get_volume_nodes(self.vol_name)
		```
