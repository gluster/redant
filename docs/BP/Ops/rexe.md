# Remote Execution Functions ( Also consists of Abstract ops functions )

[Rexe Ops](../../../common/rexe.py) contains all the functions required to carry out remote commands in the servers and client machines. 

[Abstract Ops](../../../common/ops/asbtract_ops.py) contains the functions which abstract the operations of the Rexe functions `execute_command` and `execute_command_multinode`. The abstraction handles the logginng as well as exception handling for failure based on the error_code returned.

## Given below are all the details about all the functions implemented in the Rexe Ops module:

1) **Rexe Class**<br>
        Rexe is part of the Redant mixin and hence the mixin's instantiation takes care of the required host and node details to be provided to Rexe class's constructor.

2) **establish_connection**<br>
        Establishes connection with the said set of nodes which were provided to the constructor during instantiation.

        Args:
            timeout (default value = 15)
        Returns:
            None
        Example:
            establish_connection()

3) **deconstruct_construction**<br>
        Destroys the connection which was created for a session.

        Args:
            None
        Returns:
            None
        Example:
            decontruct_connection()

4) **execute_command**<br>
        Executes the given command in the node specified.

        Args:
            cmd (str): The command to be run in the remote server.
            node (str): This is an optional parameter. If provided, the cmd will be executed in the said server or in a random server.
        Returns:
             ``` javascript
             {
               "cmd" : "<command_which_was_run>",
               "node" : "Node wherein it was run",
               "Flag" : True/False ( To check if connection failed ),
               "msg" : "<stdout response>",
               "error_msg" : "<stderr response>",
               "error_code" : BASH error code
             }
             ```
        Example:
           ```
                cmd = "<some ops command>
                ret = self.execute_command(cmd)
                # or
                ret = self.execute_command(cmd, node)
            ```

5) **execute_command_multinode**<br>
        Function to execute a remote command in multiple nodes.

        Args:
            cmd (str): Command which is to be run in the remote nodes.
            nodes (list): This is an optional parameter. If provided it will run in the given list of nodes or run the command on all nodes for a given rexe object.
        Returns:
            ``` javascript
            [ 
                {
                    "cmd" : "<command_which_was_run>",
                    "node" : "Node wherein it was run",
                    "Flag" : True/False ( To check if connection failed ),
                    "msg" : "<stdout response>",
                    "error_msg" : "<stderr response>",
                    "error_code" : BASH error code
                },
                ...
                {
                    "cmd" : "<command_which_was_run>",
                    "node" : "Node wherein it was run",
                    "Flag" : True/False ( To check if connection failed ),
                    "msg" : "<stdout response>",
                    "error_msg" : "<stderr response>",
                    "error_code" : BASH error code
                }
            ]
            ```
        Example:
            ```
            cmd = "<some ops command>
            ret = self.execute_command(cmd)
            # or
            ret = self.execute_command(cmd, node_list)
            ```

6) **execute_command_async**<br>
        Function to execute command in a node asynchronously. The async_obj returned by the function can be used to track the asynchronous operation's status and get the results.

        Args:
            cmd (str): Command which is to be run
            node (str): Optional parameter. If provided, the command will be run in the said node or else in a random node.
        Returns:
            ```javascript
            {
                "cmd" : "<command to be run>",
                "node" : "<node wherien the command is run>",
                "stdout" : "<The stdout handle>",
                "stderr" : "<The stderr handle>"
            }
            ```
        Example:
            ```
            cmd = "<some ops command>
            aync_obj = self.execute_command_async(cmd)
            # or
            async_obj = self.execute_command_async(cmd, node)
            ```

7) **check_async_command_status**<br>
        Function to check the status of the asynchronous command which was run using the execute_command_async function.

        Args:
            async_obj (dict): This dictionary was the return value of the execute_command_async function which was used to run the command whose status we are checking here.
        Returns:
            Bool value: True if the command execution has ended or False.
        Example:
            ```
            cmd = "<some ops command>
            aync_obj = self.execute_command_async(cmd)
            # or
            async_obj = self.execute_command_async(cmd, node)

            # After some other operations.....
            command_finished = self.check_async_command_status(async_obj)
            ```

8) **collect_async_result**<br>
        This function is used to collect the results of an asynchornous command execution which has completed.

        Args:
            async_obj (dict): This dictionary was the return value of the execute_command_async function which was used to run the command whose status we are checking here.
        Returns:
            ``` javascript
            {
                "cmd" : "<command_which_was_run>",
                "node" : "Node wherein it was run",
                "Flag" : True/False ( To check if connection failed),
                "msg" : "<stdout response>",
                "error_msg" : "<stderr response>",
                "error_code" : BASH error code
            }
            ```
        Example:
            ```
            cmd = "<some ops command>
            aync_obj = self.execute_command_async(cmd)
            # or
            async_obj = self.execute_command_async(cmd, node)

            # After some other operations.....
            while not self.check_async_command_status(async_obj):
                sleep(1)

            ret = self.collect_async_result(async_obj)
            ```

9) **wait_till_async_command_ends**<br>
        This function is used to wait till the asynchronous remote command execution finished and then returns the results.

        Args:
            async_obj (dict): This dictionary was the return value of the execute_command_async function which was used to run the command whose status we are checking here.
        Returns:
            ``` javascript
            {
                "cmd" : "<command_which_was_run>",
                "node" : "Node wherein it was run",
                "Flag" : True/False ( To check if connection failed),
                "msg" : "<stdout response>",
                "error_msg" : "<stderr response>",
                "error_code" : BASH error code
            }
            ```
        Example:
            ```
            cmd = "<some ops command>
            aync_obj = self.execute_command_async(cmd)
            # or
            async_obj = self.execute_command_async(cmd, node)

            # After some other operations.....
            ret = self.wait_till_async_command_ends(async_obj)
            ```
10) **transfer_file_from_local**<br>
        This function transfers the file from the local system to the specified node.

        Args:
            source_path (str): The absolute path of the file.
            dest_path (str): The absolute path of where the file is to be copied in the remote node.
            dest_node (str): The node where the file is to be transferred to.
        Returns:
            None.
        Example:
            transfer_file_from_local(source_file_path, dest_file_path, "node1")

<hr/>

## Given below are all the details about all the functions implemented in the Abstract Ops module:

1) **execute_abstract_op_node**<br>
        This function encapsulates the calls to `execute_command` and handles the exceptions on the result as well as the logging.

        Args:
            cmd (str): The command which is to be run in the remote node.
            node (str): The node wherein the command is to be run. The default value is None. None is to be given when the expectation is to run the command in a random node.
            excep (bool): An optional parameter whose default value is True. When set to False, the exception handling is not taken up and the return value is directly returned and the default behavior being when set to True, wherein the exception is handled.
        Returns:
             ``` javascript
             {
                "cmd" : "<command_which_was_run>",
                "node" : "Node wherein it was run",
                "Flag" : True/False ( To check if connection failed),
                "msg" : "<stdout response>",
                "error_msg" : "<stderr response>",
                "error_code" : BASH error code
             }
             ```
        Example:
            ```
            cmd = "<some ops command>
            ret = self.execute_abstract_op_node(cmd)
            # or
            ret = self.execute_abstract_op_node(cmd, node)
            ```

2) **execute_abstract_op_multinode**<br>
        This function encapsulates the call to `execute_command_multinode` and handles the exceptions on the result as well as the logging.

        Args:
            cmd (str): The command which is to be run in the remote nodes.
            node_list (list): List of nodes wherein this command is to be run. If kept null then the command is executed in all the servers.
        Returns:
            ``` javascript
            [ 
                {
                    "cmd" : "<command_which_was_run>",
                    "node" : "Node wherein it was run",
                    "Flag" : True/False ( To check if connection failed ),
                    "msg" : "<stdout response>",
                    "error_msg" : "<stderr response>",
                    "error_code" : BASH error code
                },
                ...
                {
                    "cmd" : "<command_which_was_run>",
                    "node" : "Node wherein it was run",
                    "Flag" : True/False ( To check if connection failed ),
                    "msg" : "<stdout response>",
                    "error_msg" : "<stderr response>",
                    "error_code" : BASH error code
                }
            ]
            ```
        Example:
            ```
            cmd = "<some ops command>
            ret = self.execute_abstract_op_multinode(cmd)
            # or
            ret = self.execute_abstract_op_multinode(cmd, node_list)
            ```
