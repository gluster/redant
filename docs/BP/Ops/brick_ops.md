# Brick Ops:

In this document, we will discuss about the set of functionalities in the brick ops. From the name itself, you can understand most of the functions but an explanation would never hurt.
The code can be found at [brick_ops.py](../../../common/ops/gluster_ops/brick_ops.py)

1) **add_brick**<br>
		This method is used to add a brick or a set of bricks as per the volume type.

		Args:
			1. volname (str): The volume in which the brick has to be added.
			2. node (str): The node on which the command is to be run.
			3. conf_hash (dict): Config hash providing parameters for adding bricks.
			4. server_list (list): List of servers provided.
			5. brick_root (list): List of brick root paths
			6. force (bool): If set to True will add force in the command being executed.
		Returns:
			A dictionary consisting                                        
            1. Flag : Flag to check if connection failed                 
            2. msg : message                                             
            3. error_msg: error message                                  
            4. error_code: error code returned                           
            5. cmd : command that got executed                           
            6. node : node on which the command got executed
		Example:
			self.add_brick(self.vol_name, self.server_list[0], conf_hash, self.server_server, self.brick_root)

2) **remove_brick**<br>
Remove brick does the opposite of add_brick operation and that is it removes existing brick or bricks from the volume. It has almost the same set of arguments apart from `option` which stores the remove brick options like start, commit, stop etc:

		Args:
			1. node (str): Node on which the command has to be executed.
			2. volname (str): The volume from which brick or a set of bricks have to be removed.
			3. conf_hash (dict):Config hash providing parameters for deleting bricks
			4. server_list (list): List of servers provided.
			5. brick_root (list): The list of brick root paths
			6. option (str): Remove brick options: <start|stop|status|commit|force>
		Returns:
			A dictionary consisting                                        
            1. Flag : Flag to check if connection failed                 
            2. msg : message                                             
            3. error_msg: error message                                  
            4. error_code: error code returned                           
            5. cmd : command that got executed                           
            6. node : node on which the command got executed
		Example:
			self.remove_brick(self.server_list[0], self.vol_name, conf_hash, self.server_server, self.brick_root, option)

## replace_brick():

This function replaces one brick with another brick or in other words, source brick with destination brick. For now, the arguments it takes include:

```m
node (str): The node on which the command has to be executed
volname (str): The volume on which the bricks have to be replaced.
src_brick (str) : The source brick name
dest_brick (str) : The destination brick name
```

### How does it work?

Its operation is quite simple. It just calls the command for replace-brick and passes the source brick path and destination brick path.
For now, you need to pass hardcoded brick path values for source and destination brick but later we will try to bring certain modifications to make this function also automated like add and remove-brick.

## reset-brick

This function resets a brick in the volume. But why do we need to reset a brick :confused:? Reset-brick is useful in case a disk goes bad etc. It provides support to reformat the disk that the brick represents in the volume. Hence, this is an important function as well to test. Let's see how we are doing it here. First, the arguments that this function need:

```m
node (str) : Node on which the command has to be executed
volname (str) : Name of the volume on which the brick
                has to be reset
src_brick (str) : Name of the source brick
dst_brick (str) : Name of the destination brick
option (str) : Options for reset brick : start | commit | force
```
It is almost same as replace-brick :nerd_face:. The arg `option` stores the option string that includes start, commit and force.

### How does it work?

It checks the value of option by comparing it with the various set of options possible and then form the command for reset-brick. If `force` value is **True** then force is appended to the command `cmd` else not. After this the command is executed to perform the reset-brick operation and the `ret` value is returned.

## form_brick_cmd()

This function helps in creating the brick command from the brick paths.
It requires the following arguments:

```m
server_list (list): List of servers
brick_root (list) : List of brick roots
volname (str) : Name of the volume
mul_fac (int) : Stores the number of bricks
                needed to form the brick command
```

### How does it work?

A loop runs from 0 to `mul_fac-1` and creates the brick command using the `server_val` and `brick_path_val`. The paths are appended in the brick_dict for the following servers and then are returned with the brick command `brick_cmd`.

## are_bricks_offline()

This function checks if the given list of bricks are offline.

```m
Args:
    volname (str) : Volume name
    bricks_list (list) : list of bricks to check
    node (str) : the node on which comparison has to be done
    strict (bool) : To check strictly if all bricks are offline
Returns:
    boolean value: True, if bricks are offline
                    False if online
```

```js
ex 1: redant.are_bricks_offline(self.vol_name, bricks_list, self.server_list[0])

ex 2: redant.are_bricks_offline(self.vol_name, bricks_list, self.server_list[0], False)
```

## check_if_bricks_list_changed()

It checks if the bricks list changed. Basically, compares the bricks list with the bricks attained from volume info.

```m
 Args:
    bricks_list: list of bricks
    volname: Name of volume
    node: Node on which to execute vol info

Returns:
bool: True is list changed
        else False
```

```js
Ex:
redant.check_if_bricks_list_changed(bricks_list, self.vol_name, self.server_list[0])
```
