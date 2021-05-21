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


