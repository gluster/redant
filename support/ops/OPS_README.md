<h1>Ops library</h1>

The Ops library consists of 2 directories:<br>

1) glusterd_ops - This directory consists of all the operations related to glusterd.<br>
2) support_ops - This directory consists of all the supporting operation libraries like performing i/o operations etc.<br>

<h3>Points of Consideration while writing Ops Library:</h3>

1) The file should be named starting with the name of the component on which the operations are written and ending with ```_ops```.<br>
2) The ops library should contain a file docstring,class docstring and a doctring for every function or operation.<br>
3) Formatted string literals have to used throughout the library and in the command creation string.<br>
4) The function declaration should contain the function name resembling the operation being performed in <u>snakecase</u>.<br>
5) Funtion parameters should be annotated with parameter types complying to PEP-3107 standard.<br>


<h3>How to write an Ops library:</h3>

1) The Ops library should start with writing a docstring for the file specifying what the file contains and which component operations does the file operations perform
    Example:
    ```
    """
    This file contains one class - PeerOps which
    holds APIS related to peers which will be called
    from the test case.
    """
    ```
2) A class should be created for the ops specifying the component whose operations are being performed ad ending with ```Ops```. The class name should be written in camel case
    Example: 
    ```
    class PeerOps
    ```
3) A docstring should be written specifying the kind of operations and functions written in the class.
    ```
    """
    PeerOps class provides APIs to perform operations
    like adding and deleting the peers,checking the status
    and list of peers in the pool.
    """
    ```
4) The funtion api should be written which performs a particular operation
5) The function api docstring must follow the following format:
    a) Description: The description must contain just the details specifying what and why the operation is being performed.<br>
    b) Args: The arguments must be specified by first writing the argument name and specifying the argument type in brackets and describing the argument.<br>
    c) Returns: The return type must be specified along with a description. If there are multiple return values then the return types must be specified along with the conditions in which  such a value is returned.<br>
    d) An example format of the return value should be specified if applicable.<br>
    e) An example for calling the function must be added if applicable.<br>
    
    Example:
    ```
    """
    Creates a cluster by probing all the nodes in the list.
    Args:
        node (list): All the nodes which form the cluster.
    Returns:
        True: If nodes are in cluster or number of nodes are 0 or 1.
        False: If cluster cannot be created.
    """
    ```

6) A string has to formed for the command which is to be executed.<br>
   If the command is a gluster command then following flags can be added:
    a) --mode=script - executes command without waiting for user input<br>
    b) --xml - Returns output in the xml format (handled by remote executioner)<br>
    
    Example:
    ```
    cmd = 'gluster pool list --xml --mode=script'
    ```
7) The command can either be run on a given node or if the node is not passed to the ops library then the node on which the command is to be run is choosed randomly by remote executioner.
8) The command is executed by calling the ```self.execute_command``` function which returns the output as a dictionary.<br>
    The different keys of the dict are:<br>
    - Flag : Flag to check if connection failed<br>
    - msg : message (can be an OrderedDict in case of gluster commands)<br>
    - error_msg: error message<br>
    - error_code: error code returned<br>
    - cmd : command that got executed<br>
    - node : node on which the command got executed<br>
     
9) The logging and the exception handling has to be done in the following way:<br>
   a) If the node parameter is optional:
   ```
    if node!=None: #if node is given
        self.logger.info(f"Running {cmd} on {node}")
        ret = self.execute_command(cmd,node)
    else: #if node is not given
        self.logger.info(f"Running {cmd} on a random node")
        ret = self.execute_command(cmd)

    if(ret['error_code']!=0): #failure case in case of non gluster command
        self.logger.error(ret['error_msg'])
        raise Exception(ret['error_msg'])    
    elif isinstance(ret['msg'],OrderedDict): #In case of executing gluster command
        if int(ret['msg']['opRet']) != 0: #failure case
            self.logger.error(ret['msg']['opErrstr'])
            raise Exception(ret['msg']['opErrstr']) #raise exception

    self.logger.info(f"Successfully ran {cmd} on {node}")
   
   ```
   b) If the node paramter is not optional:
   ```
    self.logger.info(f"Running {cmd} on {node}")

    ret = self.execute_command(node, cmd)

    if(ret['error_code']!=0):
        self.logger.error(ret['error_msg'])
        raise Exception(ret['error_msg'])    
    elif isinstance(ret['msg'],OrderedDict):
        if int(ret['msg']['opRet']) != 0:
            self.logger.error(ret['msg']['opErrstr'])
            raise Exception(ret['msg']['opErrstr'])

    self.logger.info(f"Successfully ran {cmd} on {node}")
   
   ```
   
   All the logging in the ops has to be done in the info mode . Logging in the failure case must be done in the error mode.
