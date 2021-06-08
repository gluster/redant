# Peer ops

In this document we will go throught the functionalities defined in peer ops.

## 1. peer_probe()

This function is used to probe  a peer or add a new peer to the cluster. The args that it takes:

```m
Args:
    server (str): The server to probe
    node (str): The node in the cluster where peer probe is to be run

Returns:
    ret: A dictionary consisting
        - Flag : Flag to check if connection failed
        - msg : message
        - error_msg: error message
        - error_code: error code returned
        - cmd : command that got executed
        - node : node on which the command got executed

Example:
    self.peer_probe(server, self.server_list[0])
```

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

```js
Example:
    self.peer_detach(server, self.server_list[0])
```

## 3. get_peer_status()

This function checks the status of the peer in the cluster.
It takes the node as the only arg. This node is the one on which the peer status command has to be executed.

```m
Args:
    node (str): Node on which command has to be executed.

```

It returns a list or a dictionary on the following criteria:

dict: if single peer is present in the cluster
list: if multiple peers are present in the cluster

```m
Returns:
    'peer'(list|dict): If single peer is present then dict is returned
                        If multiple peers are present then list is
                        returned
```

```js
Example:
    self.get_peer_status(self.server_list[0])
```

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

```m
Args:
    node (str): Node on which command has to be executed.

Returns:
    list: List of nodes in pool on Success, Empty list on failure.
    None on failure
```

```js
Example:
    self.nodes_from_pool_list(self.server_list[0])
```

## 5. get_pool_list()

This function parses the output received from executing `gluster pool list`. It takes `node` on which the command has to be executed as the only argument. It creates a list of dictionary on successful execution and returns it. 

```m
Args:
    node (str): Node on which command has to be executed.

Returns:
    list : list of dicts on success.
```

```js
Example:
    self.get_pool_list(self.server_list[0])
```

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

```m
Returns:
    list : list of converted IPs
```

```js
Example:

self.convert_host_to_op(self.server_list, self.server_list[0])
```


## 7. create_cluster()

This function helps in creating a cluster out of the given set of nodes irrespective of their existing cluster configurations.

It takes a list of nodes as arguments. These nodes are the ones which are going to be a part of the cluster.

```m
Args:
    node_list (list): All nodes which are to be part of the cluster.
```

It returns a boolean value, which is True if the cluster was successfully created else False.

```m
Returns:
    bool: Representing whether the cluster created failed
    or passed.
```

```js
Example:
    self.create_cluster(self.server_list)
```

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
```js
Example:
    self.delete_cluster(self.server_list)
```
## 9. is_peer_connected()

This function checks if a specific peer is connected in the cluster or attached to the cluster.

It takes the following args:
```m
 Args:
    node (str): Node from which peer status has to be executed.
    servers (str|list): A server|List of servers to be validated.
```
It returns True if the peer is connected else False.
```m
Returns
    bool : True on success (peer in cluster and connected), False on
            failure.
```

```js
Example:
    self.is_peer_connected(self.server_list, self.server_list[0])
```

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

```m
Returns:
    bool : True if all the peers are connected.
           False otherwise.
```

```js
Example:
    self.wait_for_peers_to_connect(self.server_list, self.server_list[0])
```

## 11. validate_peers_are_connected()

This function helps in validating if each server is connected to all the other servers in the cluster. 

It takes the following args:

```m
Args:
    server_list (list) : List of servers
    node (str) : node on which peer status is to be checked
```

```m
Returns (bool): True if all peers are in connected
                state with other peers.
                False otherwise.
```

```js
Example:
    self.validate_peers_are_connected(self.server_list, self.server_list[0])
```

It returns True if all the peers are in connected state else False.

## 12. peer_probe_servers()
This function probes specified servers and validate whether the probed servers are in cluster and connected state if validate is set to True.

```m

Args:
    servers (str|list): A server|List of servers to be peer probed.
    node (str): Node on which command has to be executed.
Kwargs:
    validate (bool): True to validate if probed peer is in cluster and
                        connected state. False otherwise. Default is True
    time_delay (int): time delay before validating peer status.
                        Defaults to 10 seconds.
Returns:
    bool: True on success and False on failure.
```

```js
Example:
    self.peer_probe_servers(self.server_list, self.server_list[0])
```

## 13. peer_detach_servers()
This function detaches a set of servers and validates the same if `validate` is set to `True`.

```m

Args:
    servers (str|list): A server|List of servers to be detached.
    node (str): Node on which command has to be executed.

Kwargs:
    force (bool): option to detach peer.
                  Defaults to False.
    validate (bool): True if status of the peer needs to be validated,
                     False otherwise. Defaults to True.
    time_delay (int): time delay before executing validating peer.
                      status. Defaults to 10 seconds.

Returns:
    bool: True on success and False on failure.
```

```js
Example:
    self.peer_detach_servers(self.server_list, self.server_list[0])
```

## 14. wait_till_all_peers_are_connected()

This function helps in connecting all the peers by waiting till timeout.

```m
 Args:
    server_list (str)
Returns:
    bool: True if everything is perfect. Else False
```

```js
Example:
    self.wait_till_all_peers_are_connected(self.server_list)
```