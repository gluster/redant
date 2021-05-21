# Brick Ops :bricks:

In this document, we will discuss about the set of functionalities in the brick ops. From the name itself, you can understand most of the functions but an explanation would never hurt.
Let's go through it brick by brick :smiley:

## add_brick():
This method is used to add a brick or a set of bricks as per the volume type. The arguments that it takes:

```m
volname (str): The volume in which the brick has to be added.
node (str): The node on which the command is to be run.
conf_hash (dict): Config hash providing parameters for adding
bricks.
server_list (list): List of servers provided.
brick_root (list): List of brick root paths
force (bool): If set to True will add force in the command
being executed.
```

### How does it work?

There is a counter or multiplication factor `mul_fac` which stores the count of the number of bricks for a certain volume type. `num_bricks` takes care of the number of bricks to add over the existing set of bricks.

The brick list `server_brick` is created by appending the new bricks' path and then the brick command string `brick_cmd` which is nothing but ` server:brick path ` is created. The ` brick_cmd ` is then passed to the final command `cmd` which is the complete command to be executed on the `node` to add the bricks. 

```js
brick_cmd = f"{server_val}:{brick_path_val}"

bricks_list.append(brick_cmd)
```        

After a successful execution of the command the brick_root path in the volume data structure `volds` need to be modified with the new set of bricks added.
```js
   ret = self.execute_abstract_op_node(node=node, cmd=cmd)

    self.es.add_bricks_to_brickdata(volname, server_brick)
```


## remove_brick():
Remove brick does the opposite of add_brick operation and that is it removes existing brick or bricks from the volume. It has almost the same set of arguments apart from `option` which stores the remove brick options like start, commit, stop etc:

```m
node (str): Node on which the command has to be executed.
volname (str): The volume from which brick or a set of bricks have to be removed.
conf_hash (dict):Config hash providing parameters for
                deleting bricks
brick_root (list): The list of brick root paths
option (str): Remove brick options:
            <start|stop|status|commit|force>
```

### How does it work?

It counts the number of bricks `num_brick`, creates the brick list `server_brick`, forms the brick command string `brick_cmd` and executes the final command `cmd`. After a successful operation it calls the `remove_bricks_from_brick_data` function to remove the deleted bricks from the volume data structure `volds`.
```js
ret = self.execute_abstract_op_node(node=node, cmd=cmd)
self.es.remove_bricks_from_brickdata(volname, server_brick)
```

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

This function checks if the bricks are offline. The comparison is made between the nodeCount and the number of bricks in the brick-dict. If equal that means all bricks are online else a few or all may be offline.

```m
Args:
volname (str) : Volume name
brick_dict (dict) : the brick dictionary to compare
node (str) : the node on which comparison has to be done
```