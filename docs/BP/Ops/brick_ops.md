# Brick Ops

In this document we will discuss about the set of functionalities in brick ops. From the name itself, you can understand most of them but an explanation would never hurt.
Let's go through it brick by brick :smiley:

## add_brick():
This method is used to add a brick or set of bricks as per the volume type. The arguments that it takes:

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

It counts the number of bricks `num_brick`, creates the brick list `server_brick`, forms the brick command string `brick_cmd` and executes the final command `cmd`. After a successful operation it calls the `remove_bricks_from_brick_data` function to remove the deleted bricks from the volume data structure `volds`.
```js
ret = self.execute_abstract_op_node(node=node, cmd=cmd)
self.es.remove_bricks_from_brickdata(volname, server_brick)
```