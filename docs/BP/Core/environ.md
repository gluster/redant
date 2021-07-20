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
		Modifies the volds key for a specific volume by incoming delta_value for the said 
