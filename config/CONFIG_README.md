<h1>Config File</h1>

The config file is a yaml file which defines all the configuration parameters
to create a test environment under which the test runs.
The components of the config.yml file are as follows:

<h3>1. servers_info</h3>
'servers_info' is info about each server in the cluster.<br>
Each server is defined by its ip address.
Each server should contain 4 attributes:<br>
1) ip(key representing server): ip address of the server.<br>
2) brick_root: the list of directories where bricks have to be created.<br>
3) user: the username of the server for ssh connection.<br>
4) passwd: the password of the server for ssh connection.<br>
All the above attributes have to defined by the user.<br>
If a new server has to added, then it has to follow the convention of the
previous servers

Example format of one server:<br>

ip:<br>
    &nbsp;&nbsp;&nbsp;&nbsp; brick_root: ["/bricks","/gluster"]<br>
    &nbsp;&nbsp;&nbsp;&nbsp; user: "root"<br>
    &nbsp;&nbsp;&nbsp;&nbsp; passwd: "redhat"<br>

<h3>2. clients_info</h3>
'clients_info' is info about each client in the cluster.<br>
Each client is defined by its ip address.
Each client should contain 3 attributes:<br>
1) ip: ip address of the client.<br>
2) user: the username of the client for ssh connection.<br>
3) passwd: the password of the client for ssh connection.<br>
All the above attributes have to defined by the user.<br>
If a new client has to added, then it has to follow the convention of the
previous clients 

Example format of one client:<br>

ip:<br>
   &nbsp;&nbsp;&nbsp;&nbsp; user: "root"<br>
   &nbsp;&nbsp;&nbsp;&nbsp; passwd: "redhat"<br>

<h3>3. volume_types</h3>
'volume_types' defines different volume types that we can create in
gluster and minimum number of servers are assigned to each of the
volume types to run the tests. This section is not defined by the user.
