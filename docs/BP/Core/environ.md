# Environ Methods:

The code can be found at [environ.py](../../../core/environ.py). This documentation contains the references
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
		```
			redant.es.init_ds()
		```

2) **_validate_volname**<br>
		A helper method to validate incoming volname parameter is valid or not. Exception is raised if volname is not present.
		
		Args:
			volname (str): Name of the volume.

3) **set_new_volume**<br>
		Adding the volds components for a new volume.
		
		Args:
			volname (str): Name of the volume.
			brickdata (dict): Dictionary containing objects with key as node IPs and values being list of bricks lying under that said node.

4) **reset_ds**<br>
		To reset the data structures back to an empty dictionary.

5) **get_volnames**<br>
		To obtain the list of volumes present in the volume data structure.

6) **does_volume_exists**<br>
		To check if the said volume already exists in the volds.
		
		Args:
			volname (str): Name of the volume.
			
		Returns:
			Bool value, True if volume exists or else False.

7) **remove_volume_data**<br>
		Removing a volume's data from volds.
		
		Args:
			volname (str): name of the volume.

8) **get_volume_dict**<br>
		Get the volume dictionary for requested volume.
		
		Args:
			volname (str): Name fo the volume.
		
		Returns:
			Volds specific to a volume if volume is present or else exception is thrown.

9) **get_volds**<br>
		Returning back the volds.
		
		Returns:
			volds dictionary.

10) **set_vol_type**<br>
		Modifies the volds voltype based on voltype_dict
		
		Args:
			volname (str): Name of the volume.
			voltype_dict (dict): A dictionary wherein the key is the voltype parameter name and value being the count.

11) **set_vol_type_param**<br>
		Modifies the volds key for a specific volume by incoming delta_value for the said volume.
		
		Args:
			volname (str): Name of the volume for which the voltype params have to be modified.
			voltype_key (str): The volume parameter.
			delta_value (int): The integer value which is added to the existing value for the said voltype_key.

12) **get_vol_type_param**<br>
		Obtains the value corresponding to the said volume and the voltype_key.
		
		Args:
			volname (str): Name of the volume.
			voltype_key (str): Name of the voltype.
			
		Returns:
			The value corresponding to the voltype_key and None if it doesn't exist.

13) **get_vol_type_changes**<br>
		Function to identify if there are any changes to the volumt type dictionary. More of an experimental function. Not yet completely formulated.
		
		Args:
			volname (str): Name of the volume.
			pre_voltype (dict): A volume type dictionary against which the current voltype dict of the said volname is compared.
			
		Returns:
			Bool value. True if there are any changes, else False.

14) **add_new_mountpath**<br>
		To add a new mountpath for given volume and client node.
		
		Args
			volname (str): Name of the volume.
			node (str): Node wherein the volume is mounted.
			path (str): The absolute path of the mountpoint.
		
15) **remove_mountpath**<br>
		Removes the mountpath entries under a client node for a given volume.
		
		Args:
			volname (str): Name of the volume.
			node (str): The client node.
			path (str): The path which is to be removed.
			
16) **get_mnt_pts_dict**<br>
		Method to obtain mountpath dictionary for a given volume.
		
		Args:
			volname (str): Name of the volume.
		
		Returns:
			Dicitonary of nodes and their list of mountpaths.
			
17) **get_mnt_pts_dict_in_list**<br>
		To obtain a modified list of mountpath which contains multiple client->mountpath relation.
		
		Args:
			volname (str): Name of the volume.
		
		Returns:.
			List of client->mountpath dictionaries.

18) **get_mnt_pts_list**<br>
		To obtain list of mountpath.
		
		Args:
			volname (str): Name of the volume.
			node (str): Optional parameter with default value None, The client node.
			
		Returns:
			List of mountpaths belonging to a node or list of all mountpoints when node isn't provided.

19)**add_bricks_to_brickdata**<br>
		To add a new set of bricks into the existing brick data of a volume.
		
		Args:
			volname (str): Name of the volume.
			brick_dict (dict): A dictionary of keys with node ip and values being list of bricks under that node.
			
20) **set_brickdata**<br>
		To replace the existing brickdata of a volume with whatever has been provided.
		
		Args:
			volname (str): Name of the volume
			brick_data (dict): A dictionary with keys of node ip and values being list of bricks under that node.

21) **remove_bricks_from_brickdata**<br>
		To remove the brick brickdata.
		
		Args:
			volname (str): Name of the volume.
			brick_data (dict): A dictionary with keys of node ip and values being list of bricks under that node.

22) **get_brickdata**<br>
		To obtain the brick dictionary of a certain volume.
		
		Args:
			volname (str): name of the volume.
		
		Returns:
			Dictionary of keys of node ip and values being list of bricks under that node.

23) **get_all_bricks_list**<br>
		To create a list of node->brick list for a given volume.
		
		Args:
			volname (str): Name of the volume.
		
		Returns:
			List of node:brick values.

24) **get_brick_list**<br>
		Method to obtain the list of bricks for a given volume and node.
		
		Args:
			volname (str): Name of the volume
			node (str): Node for which the brick data is required.
			
		Returns:
			list of bricks for the given node.

25) **set_volume_start_status**<br>
		To set the volume start status of a given volume to True or False.
		
		Args:
			volname (str): Name of the volume.
			state (bool): The state can be True or False.
		
26) **get_volume_start_status**<br>
		To get the volume start status of the volume mentioned.
		
		Args:
			volname (str): Name of the volume.
		
		Returns:
			bool value representing the status of the volume.
			
27) **set_vol_option**<br>
		To set a volume option for said volume based on the dictionary of options provided.
		
		Args:
			volname (str): Name of the volume.
			options_dict (dict): Dictionary wherein key values are the options and the values being the option's values.

28) **set_vol_options_all**<br>
		To set options in the clusteropt dict.
		
		Args:
			option_dict (dict): Dictionary of cluster options and their corresponding values.

29) **reset_vol_options_all**<br>
		To delete the clusteropts based on the option_list provided.
		
		Args:
			option_list (list): List of options which have to be removed from the clusteropts.

30) **get_vol_options**<br>
		To obtain the volume options changed during the test case run.
		
		Args:
			volname (str): Name of the volume.
			
		Returns:
			Dictionary of options for a given volume.

31) **get_vol_options_all**<br>
		To return the cluster options dictionary.
		
		Returns:
			Dictionary of cluster options.

32) **is_volume_options_populated**<br>
		To check whether the volume options of a given volume is populated or empty.
		
		Args:
			volname (str): Name of the volume.
		
		Returns:
			bool value. True if populated or else False.

33) **_reset_all_options_in_a_vol**<br>
		To reset all options of a given volume.
		
		Args:
			volname (str): Reset the volume options under a volume.

34) **reset_volume_option**<br>
		To reset the options of volumes based of volume name and the option provided.
		
		Args:
			volname (str): Name of the volume
			option (str): The option name.

35) **get_volume_nodes**<br>
		To get all the nodes whose bricks are part of a volume.
		
		Args:
			volname (str): Name fo the volume.
		
		Returns:
			List of nodes whose bricks are parts of the volume.
