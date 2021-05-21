# Peer ops

In this document we will go throught the functionalities defined in peer ops.

## 1. peer_probe()

This function is used to probe  a peer or add a new peer to the cluster. The args that it takes:

```m
Args:
    server (str): The server to probe
    node (str): The node in the cluster where peer probe is to be run
```

It returns a boolean value: True if the probe was successful, False if not.

## 2. peer_detach()

This function helps in detaching a node or peer from the cluster.
The arguments that is takes:

```m
Args:
    server (str): Server to be detached from the cluster
    node (str): Node on which command has to be executed.
    force (bool): if set to true will exceute the peer
                    detach command with force option.

Kwargs:
    force (bool): option to detach peer. Defaults to False.
```

It returns a dictionary `ret` which includes the following:

```m
    Flag : Flag to check if connection failed
    msg : message
    error_msg: error message
    error_code: error code returned
    cmd : command that got executed
    node : node on which the command got executed
```

## 3. get_peer_status()

This function checks the status of the peer in the cluster.
It takes the node as the only arg. This node is the one on which the peer status command has to be executed.

It returns a list or a dictionary on the following criteria:

dict: if single peer is present in the cluster
list: if multiple peers are present in the cluster


## 4. nodes_from_pool_list():

This functions provides a list of servers in the `gluster pool list`.

Just for reference 
```m
[root@server1 tmp]# gluster pool list
UUID                           Hostname        State
xxxxxx-xxxxx-xxxxxx-xxxxxxx    server2         Connected 
xxxxxx-xxxxx-xxxxxx-xxxxxxx    localhost       Connected 
```

It takes the node on which the command has to be run as the only args.
It returns a list of nodes in the pool on successful execution while an empty list on failure.

## 5. get_pool_list()

This function parses the output received from executing `gluster pool list`. It takes `node` on which the command has to be executed as the only argument. It creates a list of dictionary on successful execution and returns it. 

## 6. convert_hosts_to_ip()

If you have already gone through the docstring, you might not even need to read this :sweat_smile:. 

This function converts hostnames to their respective IP addresses.

It takes the following arguments:
```m
node_list (list): List of nodes obtained wherein the node can
                  be represented by ip or hostname.
node (str): The node which is represented by localhost. Has to
            be replaced by corresponding IP.
```

It returns a list consisting of the converted IP addresses.

## 7. create_cluster()

This function helps in creating a cluster out of the given set of nodes irrespective of their existing cluster configurations.

It takes a list of nodes as arguments. These nodes are the ones which are going to be a part of the cluster.

```m
Args:
    node_list (list): All nodes which are to be part of the cluster.
```

It returns a boolean value, which is True if the cluster was successfully created else False.

## 8. delete_cluster()

This functions helps in deleting the cluster or in other words, breaking down the cluster.

It takes the following args:
```m
Args:
    node_list (list) : List of nodes which are part of a cluster
                       which is to be broken up.
```
This node_list contains the nodes that are a part of the cluster.
These nodes are detached one by one from the cluster.

## 9. is_peer_connected()

This function checks if a specific peer is connected in the cluster or attached to the cluster.

It takes the following args:
```m
 Args:
    node (str): Node from which peer status has to be executed.
    servers (str|list): A server|List of servers to be validated.
```
It returns True if the peer is connected else False.

## 10. wait_for_peers_to_connect()

This function checks if the node is connected in the cluster with a timeout(wait-timeout). On success, it returns True else completes the number of iterations and in case of peer not getting connected returns False.

It takes the following args:
```m
Args:
    node: node on which cmd has to be executed.
    servers (str|list): A server|List of server hosts on which peer
        status has to be checked.
    wait_timeout: timeout to retry connected status check in node.
```

## 11. validate_peers_are_connected()

This function helps in validating if each server is connected to all the other servers in the cluster. 

It takes the following args:

```m
Args:
    server_list (list) : List of servers
    node (str) : node on which peer status is to be checked
```

It returns True if all the peers are in connected state else False.
