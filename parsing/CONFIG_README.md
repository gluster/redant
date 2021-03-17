<h1>Config File</h1>

The config file is a yaml file which defines all the configuration parameters
to create a test environment under which the test runs.
The components of the config.yml file are as follows:

<h3>1. servers</h3>
The servers section consists of all server ip addresses which run the glusterd
service and provide a storage environment to which the clients mount their 
filesystem.
A single server in the config file has to be specified with a reference name 
followed by ip address in the following way:<br>
`&server_vm1 0.0.0.0`<br>
server_vm1 is a reference to its ip address which can be used to refer to its 
ip address in the further config file or in the test cases. 1 should be replaced
by other integers in the increasing order while specifying further servers

<h3>2. clients</h3>
The clients section consists of all client ip addresses whose file system has to
be mounted to the glusterfs servers.
A single client in the config file has to be specified with a reference name 
followed by ip address in the following way:<br>
`&client_vm1 0.0.0.0` <br>
client_vm1 is a reference to its ip address which can be used to refer to its 
ip address in the further config file or in the test cases. 1 should be replaced
by other integers in the increasing order while specifying further clients.

<h3>3. servers\_info</h3>
The 'servers\_info' consists of brick\_root for each server which is a list 
of all the mount points in the client. 
The brick\_root list has to be specified in the following way:<br>
`brick_root: ["/bricks1","/bricks2"]`<br>
username and password can also be defined for creating ssh connection.

<h3>4. clients\_info</h3>
 'clients\_info' is info about each client in  the cluster.
 The info should contain platform(linux),super_user name(root
 in case of linux) as mentioned in the config file.
 username and password can also be defined for creating ssh connection.
