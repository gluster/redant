<h1>Config File</h1>

The config file is a yaml file which defines all the configuration parameters
to create a test environment under which the test runs.
The components of the config.yml file are as follows:

<h3>1. servers_info</h3>
'servers_info' is info about each server in the cluster.<br>
Each server is defined by its ip address which acts as a key representing the server.<br>
Each server should contain 1 attribute:<br>
1) brick_root: the list of directories where bricks have to be created.<br>
The above attribute has to be defined by the user.<br>
If a new server has to added, then it has to follow the convention of the
previous servers.

Example format of one server:<br>

ip:<br>
    &nbsp;&nbsp;&nbsp;&nbsp; brick_root: ["/bricks","/gluster"]<br>

<h3>2. clients_info</h3>
'clients_info' is info about each client in the cluster.<br>
Each client is defined by its ip address which acts as a key representing the client.<br>
The client does not take any attribute values.<br>
If a new client has to added, then it has to follow the convention of the
previous clients. 

Example format of one client:<br>

ip:<br>

<h3>3. volume_types</h3>
'volume_types' defines different volume types that we can create in
gluster and minimum number of servers are assigned to each of the
volume types to run the tests. This section is not defined by the user.

<h3>4. excluded_tests</h3>
'excluded_tests' is a list of tests given by the user which are excluded during
the test run. Each element of the list consists of the complete path of the test
case with respect to the redant directory.

Specific design consideration and more information on the feature is given in
the doc link [here](https://docs.google.com/document/d/1T0Fu20WzH7jACE9wTVT_SEyfrcXKQUmEExpLKru6Ys0/edit?usp=sharing)

Example format of excluded_tests list:<br>

excluded_tests:<br>
    &nbsp;&nbsp;&nbsp;&nbsp; - tests/functional/glusterd/test1<br>
    &nbsp;&nbsp;&nbsp;&nbsp; - tests/functional/afr/test2<br>
    *To exclude a complete directory or it's subdirectories*
    &nbsp;&nbsp;&nbsp;&nbsp; - tests/functional/afr<br>
