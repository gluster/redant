<h1>Config File</h1>

The config file is a yaml file which defines all the configuration parameters
to create a test environment under which the test runs.
The components of the config.yml file are as follows:

<h3>1. servers_info</h3>
'servers_info' is info about each server in the cluster.<br>
Each server should contain 4 attributes:<br>
1) ip: ip address of the server.<br>
2) brick_root: the list of directories where bricks have to be created.<br>
3) user: the username of the server for ssh connection.<br>
4) passwd: the password of the server for ssh connection.<br>
All the above attributes have to defined by the user.<br>
If a new server has to added, then it has to follow the convention of the
previous servers and the name for each server has to be given in the format
"server<num>" where num(number) is given in numerological order.<br>

Example format of one server:<br>

server1:
    &nbsp;&nbsp;&nbsp;&nbsp; ip: "1.1.1.1"
    &nbsp;&nbsp;&nbsp;&nbsp; brick_root: ["/bricks","/gluster"]
    &nbsp;&nbsp;&nbsp;&nbsp; user: "root"
    &nbsp;&nbsp;&nbsp;&nbsp; passwd: "redhat"

<h3>2. clients_info</h3>
'clients_info' is info about each server in the cluster.<br>
Each server should contain 3 attributes:<br>
1) ip: ip address of the server.<br>
2) user: the username of the server for ssh connection.<br>
3) passwd: the password of the server for ssh connection.<br>
All the above attributes have to defined by the user.<br>
If a new client has to added, then it has to follow the convention of the
previous clients and the name for each client has to be given in the format
"client<num>" where num(number) is given in numerological order.<br>

Example format of one client:<br>

client1:
   &nbsp;&nbsp;&nbsp;&nbsp; ip: "5.5.5.5"
   &nbsp;&nbsp;&nbsp;&nbsp; user: "root"
   &nbsp;&nbsp;&nbsp;&nbsp; passwd: "redhat"

<h3>3. volume_types</h3>
'volume_types' defines different volume types that we can create in
gluster and minimum number of servers are assigned to each of the
volume types to run the tests. This section is not defined by the user.
