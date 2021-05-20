# Remote Execution Functions

This document is specific to the functions dealing with the remote
execution operations, what are their arguments, parameters and how to use
them along with example.

1. Rexe Class
Why are we having a description about a class when we stated this document
consists of functions falling under the category of remote execution
operations ? Well, because the remote execution opeations can be performed
only when an object for the Rexe class is instantiated. Now for people writing
test cases, this is not directly visible as to where and how the connection
is established as it is handled by the framework. To put it in short words,
Rexe is part of the Redant mixin and hence the mixin's instantiation takes
care of the required host and node details to be provided to Rexe.

2. `establish_connection`
* Parameters: timeout (default value = 15)
* Return value: None
* Purpose: this method is used to establish the connection with a said set of
nodes which has been provided to the Rexe class during mixin creation.
* When can I use it : To be honest, unless and until we come up with a scenario
in a test case which requires establishing new connections, don't go around 
playing with this function as this is mostly used within the framework.

3. `deconstruct_construction`
* Parameters: None
* Return value: None
* Purpose: this method will shutdown the remote connections which were
established with the help of Rexe.
* When can I use it : For test cases, again, unless and until you need it, I'd
recommend not to play around with it as there would be some serious 
consequences. ( Kiddin, the only consequence is that the test cases will fail,
and some strange exception will be thrown )

4. `execute_command`
* Parameters: 
    Type 1: a) Command to run in string
    Type 2: a) Command to run in string
            b) node where the command has to be run in string
* Return value: A dictionary of the following form,

 ``` javascript
 {
   "cmd" : "<command_which_was_run>",
   "node" : "Node wherein it was run",
   "Flag" : True/False,
   "msg" : "<stdout response>",
   "error_msg" : "<stderr response>",
   "error_code" : BASH error code
 }
 ```

wherein,
-> cmd is the command which we gave the method to run in the very first place.
-> node is where the command was run
-> Flag is True if the command was successful or False when it isn't
-> msg is the stdout response received after the command run is finished.
-> error_msg is the stderr response received after the command run is finished.
-> error_code is the standard BASH return value for the said command after it
has run its course.
* Purpose: this method is overloaded and hence has two forms, one wherein the
user has to pass on the node wherein they specifically want to run their 
command and the other type wherein the user leaves the decision of where to
run the command upto the framework as it feels that it actually doesn't matter
where the command is run in a given list of servers.
If the node wherein the command has to be executed is due to some reason
disconnected, then a reconnect is attempted inside this function. Though the
current design doesn't have re-tries and on failure to connect an exception
will be thrown.
* When can I use it : Now the understanding is that the response returned by
these functions are still raw as we don't validate whether the command was a 
success or failure. If the user wants those validations then this isn't the
method to use whereas if they want to directly handle the validations instead
of leaving the command status validation to a try-except validation layer,
this can be used.
But that said, this function was mainly envisaged to be used by gluster related
ops functions. these ops functions will usually create the cmd but use the
`execute_command` to actually execute those commands in the remote servers.
* Example:

-> Whether we use is inside an ops or directly in a test case ( in case of a 
test case, use `redant.` instead of `.self`),

```
cmd = "<some ops command>
ret = self.execute_command(cmd)
# or
ret = self.execute_command(cmd, node)
```

5. `execute_command_async`
* Parameters: 
    Type 1: a) Command to be run in string.
    Type 2: a) Command to be run in string, b) node wherein the command is to
               be run.
* Return value: The `execute_command_async` returns a async_object which is
basically a dictionary in both the overloaded forms of the method.

```javascript
{
  "cmd" : "<command to be run>",
  "node" : "<node wherien the command is run>",
  "stdout" : "<The stdout handle>",
  "stderr" : "<The stderr handle>"
}
```

Now herein,
-> cmd is the command which is run in the remote server
-> node is wherein the command is to be run
-> stdout handle is the stdout object we receive after giving a request for
command execution.
-> stderr handle is the stderr object we receive after giving a request for
command execution.
* Purpose: The async flavour functions were added so as to handle the commands
asynchronously. Hence one can request for a certain command to be executed in
a certain server, then move on to other tasks rather than waiting for the
response and then once the value is required they can come and check whether
the response of the asynchronous task they had given has completed or still
running. Now this function is the first step in this design flow. Initiating a
remote execution command in a said node.
Similar to the design of `execute_command`, we have two flavours of this method
one with a specific request to run the command in a particular node and another
wherein we just leave it to the framework and lady luck.
If there is any network disconnect before this command execution request has
to be given, then this method will attempt a reconnect once. Then it goes on to
throw an exception.
* When can I use it: Whenever there is a need in the test case or ops to have
a certain command to be run in background while some other command is to be run
in foreground, this is the go to function. But along with this function, one
would also need to use the other allied functions about which we will talk
below.
* Example:

-> Whether we use is inside an ops or directly in a test case ( in case of a 
test case use `redant.` instead of `self.`),

```
cmd = "<some ops command>
aync_obj = self.execute_command_async(cmd)
# or
async_obj = self.execute_command_async(cmd, node)
```

6. `check_async_command_status`
* Parameter: async object which was received after a request for async command
execution was requested.
* Return value: True if the command has been completed else False.
* Purpose: After a request has been put for the execution of an async command,
we need to check when it has finished execution and what is its current running
status.
* Where can I use it: This method can be used in ops as well as in test cases
if the need is to check whether the async command has finished execution or
not.
* Example:

-> Whether we use is inside an ops or directly in a test case ( in case of
a test case use `redant.` instead of `self.`),

```
cmd = "<some ops command>
aync_obj = self.execute_command_async(cmd)
# or
async_obj = self.execute_command_async(cmd, node)

# After some other operations.....
command_finished = self.check_async_command_status(async_obj)
```

7. `collect_async_result`
* Parameter: async object which was received after a request for async command
execution was requested.
* Return value:

 ``` javascript
 {
   "cmd" : "<command_which_was_run>",
   "node" : "Node wherein it was run",
   "Flag" : True/False,
   "msg" : "<stdout response>",
   "error_msg" : "<stderr response>",
   "error_code" : BASH error code
 }
 ```

wherein,
-> cmd is the command which we gave the method to run in the very first place.
-> node is where the command was run
-> Flag is True if the command was successful or False when it isn't
-> msg is the stdout response received after the command run is finished.
-> error_msg is the stderr response received after the command run is finished.
-> error_code is the standard BASH return value for the said command after it
has run its course.
* Purpose: The purpose of this method is to collect the results after the
asynchronous command has been executed.
* Where can I use it: We can use this along with the `execute_command_async`,
as result collection is not handled by the `execute_command_async` hence the
requirement for a separate function to obtain the results and pass it on after
the execution has been finished. This can be used both at ops as well as
test case level.
* Example:

-> Whether we use is inside an ops or directly in a test case ( in case of
a test case use `redant.` instead of `self.`),

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

8. `wait_till_async_command_ends`
* Parameter: The async object which was received from the
`execute_command_async`
* Return value: 
 
``` javascript
 {
   "cmd" : "<command_which_was_run>",
   "node" : "Node wherein it was run",
   "Flag" : True/False,
   "msg" : "<stdout response>",
   "error_msg" : "<stderr response>",
   "error_code" : BASH error code
 }
 ```

wherein,
-> cmd is the command which we gave the method to run in the very first place.
-> node is where the command was run
-> Flag is True if the command was successful or False when it isn't
-> msg is the stdout response received after the command run is finished.
-> error_msg is the stderr response received after the command run is finished.
-> error_code is the standard BASH return value for the said command after it
has run its course.
* Purpose: This method logically encapsultes the operations of two other
methods, `check_async_command_status` and `collect_async_result`. So, 
technically this is equivalent to telling the framework that I want to wait
till I receive a response for the said asynchronous command which I had
requested for.
* Where can I use it: Again, ops or test cases, go crazy ( according to
requirement ).
* Example:

-> Whether we use is inside an ops or directly in a test case ( in case of
a test case use `redant.` instead of `self.`),

```
cmd = "<some ops command>
aync_obj = self.execute_command_async(cmd)
# or
async_obj = self.execute_command_async(cmd, node)

# After some other operations.....
ret = self.wait_till_async_command_ends(async_obj)
```

9. `execute_command_multinode`
* Parameter: With overloaded flavour,
    Type 1: a) Command which is to be run in string.
    Type 2: a) Command which is to be run in string.
            b) The list of nodes wherein the commands are to be run. This will
            be a list of strings representing node IPs.
* Return value: Is a list of dictionaries.
 
``` javascript
[ 
{
   "cmd" : "<command_which_was_run>",
   "node" : "Node wherein it was run",
   "Flag" : True/False,
   "msg" : "<stdout response>",
   "error_msg" : "<stderr response>",
   "error_code" : BASH error code
 },
...
{
   "cmd" : "<command_which_was_run>",
   "node" : "Node wherein it was run",
   "Flag" : True/False,
   "msg" : "<stdout response>",
   "error_msg" : "<stderr response>",
   "error_code" : BASH error code
 }
]
 ```

wherein inside the dictionary,
-> cmd is the command which we gave the method to run in the very first place.
-> node is where the command was run
-> Flag is True if the command was successful or False when it isn't
-> msg is the stdout response received after the command run is finished.
-> error_msg is the stderr response received after the command run is finished.
-> error_code is the standard BASH return value for the said command after it
has run its course.

We have multiple dictionaries wherein each dictionary object pertains to a node
which was provided as part of the list when the method was initially called.

* Purpose: this method is overloaded and hence has two forms, one wherein the
user has to pass on the list of nodes wherein they specifically want to run
their command and the other type wherein the user wants it to be run in all 
servers.
One point to note is that this method internally invokes `execute_command`.
* When can I use it : Now the understanding is that the response returned by
these functions are still raw as we don't validate whether the command was a 
success or failure. If the user wants those validations then this isn't the
method to use whereas if they want to directly handle the validations instead
of leaving the command status validation to a try-except validation layer,
this can be used.
But that said, this function was mainly envisaged to be used by gluster related
ops functions. these ops functions will usually create the cmd but use the
`execute_command_multinode` to actually execute those commands in the 
remote servers.
* Example:

-> Whether we use is inside an ops or directly in a test case ( in case of a 
test case, use `redant.` instead of `.self`),

```
cmd = "<some ops command>
ret = self.execute_command(cmd)
# or
ret = self.execute_command(cmd, node_list)
```

10. `execute_abstract_op_node`
* Parameters:
    a) cmd which is to be executed at the said node in string.
    b) node wherein the command is to be executed. This parameter can be
       ignored and the default value is None.
* Return valus: 

 ``` javascript
 {
   "cmd" : "<command_which_was_run>",
   "node" : "Node wherein it was run",
   "Flag" : True/False,
   "msg" : "<stdout response>",
   "error_msg" : "<stderr response>",
   "error_code" : BASH error code
 }
 ```

wherein,
-> cmd is the command which we gave the method to run in the very first place.
-> node is where the command was run
-> Flag is True if the command was successful or False when it isn't
-> msg is the stdout response received after the command run is finished.
-> error_msg is the stderr response received after the command run is finished.
-> error_code is the standard BASH return value for the said command after it
has run its course.

* Purpose: This method encapsulates the calls to the `execute_command`. And
was created to reduce the code duplicity seen in the handling of the 
exceptions seen across the ops functions whenever the command execution
had failed at the server.
* When can I use it : This is the standard function which can be used if the
user doesn't want to go ahead in the test case flow if the operation which had
been requested has failed. If the `execute_command` sends back a response
wherein the error code is assigned some value other than 0 ( which means
success ), then this method will raise an exception.
* Example:

-> Whether we use is inside an ops or directly in a test case ( in case of a 
test case, use `redant.` instead of `.self`),

```
cmd = "<some ops command>
ret = self.execute_abstract_op_node(cmd)
# or
ret = self.execute_abstract_op_node(cmd, node)
```


11. `execute_abstract_op_multinode`
This method is similar to `execute_abstract_op_node` and forms an abstraction
layer over the method `execute_command_multinode`. Rather than repeating the
terminologies again, I'll let the user to refer to these methods.
