# Volume Ops

[Volume Ops](../../../common/ops/gluster_ops/volume_ops.py) contains all the functions required to carry out the volume related operations. Given below are all the details about all the functions implemented in the Volume Ops module:

1) **volume_mount**<br>
        Mounts the gluster volume to the client's filesystem.

        Args:
            server (str): Hostname or IP address
            volname (str): Name of volume to be mounted
            path (str): The path of the mount directory(mount point)
        Kwargs:
            node (str): The client node in the cluster where volume
                        mount is to be run. Default - None
        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        Example:
            volume_mount(self.server_list[0], self.vol_name, self.mountpoint, self.client_list[0])

2) **volume_unmount**<br>
    Unmounts the gluster volume from its client.

        Args:
            volname (str): The volume whose mt pt. is to be unmounted.
            path (str): The path of the mount directory(mount point)
        Kwargs:
            node (str): The client node in the cluster where volume
                        unmount is to be run. Default - None
        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        Example:
            volume_unmount(self.vol_name, self.mountpoint, self.client_list[0])

3) **volume_create**<br>
    Create the gluster volume with specified configuration

        Args:
            volname(str): volume name that has to be created
            node(str): server on which command has to be executed
            conf_hash (dict): Config hash providing parameters for volume
            creation.
            server_list (list): List of servers
            brick_root (list): List of root path of bricks
        Kwargs:
            force (bool): If this option is set to True, then create volume
                          will get executed with force option. Default - False
        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        Example:
            volume_type1 = 'dist'
            volume_name1 = f"{self.test_name}-{volume_type1}-1"
            volume_create(volume_name1, self.server_list[0],
                          self.vol_type_inf[self.conv_dict[volume_type1]],
                          self.server_list, self.brick_roots, True)

4) **volume_start**<br>
    Starts the gluster volume

        Args:
            volname (str): Name of the volume to start
        Kwargs:
            node (str): Node on which cmd has to be executed. Default - None
            force (bool): If this option is set to True, then start volume
                will get executed with force option. If it is set to False,
                then start volume will get executed without force option.
                Default - False
        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        Example:
            volume_start(self.vol_name,self.server_list[0])

5) **volume_stop**<br>
    Stops the gluster volume

        Args:
            volname (str): Name of the volume to stop
        Kwargs:
            node (str): Node on which cmd has to be executed. Default - None
            force (bool): If this option is set to True, then start volume
                will get executed with force option. If it is set to False,
                then start volume will get executed without force option
        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        Example:
            volume_stop(self.vol_name, self.server_list[0], True)

6) **volume_delete**<br>
    Deletes the gluster volume if given volume exists in gluster.

        Args:
            volname (str): Name of the volume to delete
        Kwargs:
            node (str): Node on which cmd has to be executed. Default - None
        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        Example:
            volume_delete(self.vol_name, self.server_list[0])

7) **volume_delete_and_brick_cleanup**<br>
    Deletes the gluster volume if given volume exists in gluster.

        Args:
            volname (str): Name of the volume to delete
        Kwargs:
            node (str): Node on which cmd has to be executed. Default - None
        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        Example:
            volume_delete_and_brick_cleanup(self.vol_name, self.server_list[0])

8) **get_volume_info**<br>
    Gives volume information.

        Kwargs:
            node (str): Node on which cmd has to be executed. Default - None
            volname (str): volume name. Default - 'all'
        Returns:
            dict: a dictionary with volume information.
        Example:
            get_volume_info(server)
            >>>{'test-vol1': {
                               'id': '6c0053a5-d11c-4ba0-ae5e-f5d5e43a4116',
                               'status': '0',
                               'statusStr': 'Created',
                               'snapshotCount': '0',
                               'brickCount': '2',
                               'bricks': [{
                                            'name': 'server-vm1:/brick1',
                                            'isArbiter': '0',
                                            '#text': 'server-vm1:/brick1'
                                           },
                                           {'name': 'server-vm1:/brick3',
                                            'isArbiter': '0',
                                            '#text': 'server-vm1:/brick3'
                                            }],
                               'optCount': '4',
                               'options': {
                                            'storage.fips-mode-rchecksum': 'on',
                                            'transport.address-family': 'inet',
                                            'nfs.disable': 'on',
                                            'snap-activate-on-create': 'enable'}
                             },
                'test-vol2': {
                               'id': 'd5b365b5-10f6-46db-a72d-259859c413af',
                               'status': '0',
                               'statusStr': 'Created',
                               'snapshotCount': '0',
                               'brickCount': '1',
                               'bricks': [{
                                            'name': 'server-vm1:/brick2',
                                            'isArbiter': '0',
                                            '#text': 'server-vm1:/brick2'
                                           }],
                               'optCount': '4',
                               'options': {
                                            'storage.fips-mode-rchecksum': 'on',
                                            'transport.address-family': 'inet',
                                            'nfs.disable': 'on',
                                            'snap-activate-on-create': 'enable'
                                           }
                             }
               }

9) **get_volume_list**<br>
    Fetches the volume names in the gluster.
        Uses xml output of volume list and parses it into to list

        Kwargs:
            node (str): Node on which cmd has to be executed. Deault - None
        Returns:
            list: List of volume names
        Example:
            get_volume_list(server)
            >>>['testvol1', 'testvol2']

10) **volume_reset**<br>
    Resets the gluster volume of all the reconfigured options.

        Args:
            volname (str): Name of the volume to reset
        Kwargs:
            node (str): Node on which cmd has to be executed. Default - None
            force (bool): If this option is set to True, then reset volume will get
                          executed with force option. If it is set to False, then reset
                          volume will get executed without force option. Default - False
        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        Example:
            volume_reset(self.vol_name,self.server_list[0])

11) **get_volume_status**<br>
    Gets the status of all or the specified volume

        Kwargs:
            volname (str): volume name. Default - 'all'
            node (str): Node on which cmd has to be executed. Default - None
            service (str): name of the service to get status.
                service can be, \[nfs|shd|<BRICK>|quotad\], If not given,
                the function returns all the services. Default - ''
            options (str): options can be,
                \[detail|clients|mem|inode|fd|callpool|tasks\]. If not given,
                the function returns the output of gluster volume status. Default - ''
            excep (bool): exception flag to bypass the exception if the
                          cmd fails. If set to False the exception is
                          bypassed and value from remote executioner is
                          returned. Defaults to True
        Returns:
            dict: volume status in dict of dictionary format
            None: In case no volumes are present
        Example:
            get_volume_status("test-vol1",self.server_list[0])
            >>>{ 'test-vol1': {
                                'nodeCount': '2',
                                'node': [{
                                           'hostname': 'server-vm1',
                                           'path': '/brick1',
                                           'status': '1',
                                           'port': '49152',
                                           'ports': {
                                                      'tcp': '49152',
                                                      'rdma': 'N/A'
                                                    },
                                           'pid': '669291'
                                         },                                          
                                         {
                                           'hostname': 'server-vm1',
                                           'path': '/brick3',
                                           'status': '1',
                                           'port': '49153',
                                           'ports': {
                                                      'tcp': '49153',
                                                      'rdma': 'N/A'
                                                     },
                                           'pid': '669307'
                                         }],
                                'tasks': None
                              }
               }

12) **get_volume_options**<br>
     Gets the option values for a given volume.

        Args:
            volname (str): volume name
        Kwargs:
            option (str): volume option to get status.
                        If not given, the function returns all the options for
                        the given volume. Default - 'all'
             node (str): Node on which cmd has to be executed. Deafult - None
        Returns:
            dict: value for the given volume option in dict format, on success
            NoneType: on failure
        Example:
            get_volume_options(self.server_list[0])
            >>>{ 
                 'cluster.server-quorum-ratio': '51 (DEFAULT)',
                 'cluster.enable-shared-storage': 'disable (DEFAULT)',
                 'cluster.op-version': '100000',
                 'cluster.max-op-version': '100000',
                 'cluster.brick-multiplex': 'disable (DEFAULT)',
                 'cluster.max-bricks-per-process': '250 (DEFAULT)',
                 'glusterd.vol_count_per_thread': '100 (DEFAULT)',
                 'cluster.localtime-logging': 'disable (DEFAULT)',
                 'cluster.daemon-log-level': 'INFO (DEFAULT)',
                 'cluster.brick-graceful-cleanup': 'disable (DEFAULT)'
               }

13) **set_volume_options**<br>
     Sets the option values for the given volume.

        Args:
            volname (str): volume name
            options (dict): volume options in key value format
        Kwargs:
            node (str): Node on which cmd has to be executed. Default - None
        Example:
            options = {"user.cifs":"enable","user.smb":"enable"}
            set_volume_options("test-vol1", options, self.server_list[0])

14) **validate_volume_option**<br>
     Validate the volume options

        Args:
            volname (str) : volume name
            options (dict) : dictionary of options which are to be validated.
        Kwargs:
            node (str) : Node on which cmd has to be executed. Default - None
        Returns:
            No value if success or else ValueError will be raised.
        Example:
            options = {"user.cifs":"enable","user.smb":"enable"}
            validate_volume_option(sel.vol_name, options)
            

15) **reset_volume_option**<br>
    Resets the volume option

        Args:
            volname (str): volume name
            option (str): volume option
        Kwargs:
            node (str): Node on which cmd has to be executed. Default - None
            force (bool): If this option is set to True, then reset volume
                will get executed with force option. If it is set to False,
                then reset volume will get executed without force option.
                Default - False
        Example:
            reset_volume_option("test-vol1", "option", server)

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
         Example:
            

16) **volume_sync**<br>
	    Sync the volume to the specified host
    
        Args:
            hostname (str): host name to which volume has to be sync'ed
            node (str): Node on which cmd has to be executed.
        Kwargs:
            volname (str): volume name. Defaults to 'all'.
        Example:
            volume_sync(volname="testvol",server)

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
         Example:
            volume_sync(hostname,self.server_list[0])

17) **is_volume_started**<br>
		Function to check whether a said volume is in started state.

		Args:
			1. volname (str): The name of the volume
			2. node (str): node wherein the command is to be run
		Returns:
			True if in Started state else False
		Example:
			self.is_volume_started(self.vol_name, self.server_list[0])

18) **wait_for_vol_to_go_offline**<br>
		Function to wait till the said volume goes offline.

		Args:
			1. volname (str): Name of the volume.
			2. node (str): Node wherein the command is to be checked.
			3. timeout (int): Optional argument with default value of 120. Function will wait for at max the timeout value for the volume to go offline.
		Returns:
			True if it goes offline, else False
		Example:
			self.wait_for_vol_to_go_offline(self.vol_name, self.server_list[0])

18) **wait_for_vol_to_come_online**<br>
		Function to wait till the said volume comes online.

		Args:
			1. volname (str): Name of the volume.
			2. node (str): Node wherein the command is to be checked.
			3. timeout (int): Optional argument with default value of 120. Function will wait for at max the timeout value for the volume to comes online.
		Returns:
			True if it comes online, else False
		Example:
			self.wait_for_vol_to_come_online(self.vol_name, self.server_list[0])

19) **setup_volume**<br>
        Function to setup the gluster volume with the specified configuration.

        Args:
            1. volname(str): volume name that has to be created
            2. node(str): server on which command has to be executed
            3. conf_hash (dict): Config hash providing parameters for volume
                                 creation.
            4. server_list (list): List of servers
            5. brick_root (list): List of root path of bricks
            6. force (bool): If this option is set to True, then create volume
                             will get executed with force option.
            7. create_only (bool): True, if only volume creation is needed.
                                   False, will do volume create, start, set
                                   operation if any provided in the volume_config
                                   By default, value is set to False.
            8. excep (bool): exception flag to bypass the exception if the
                          setup volume command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True
        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        Example:
            self.volume_type1 = 'dist'
            self.volume_name1 = f"{self.test_name}-{self.volume_type1}-1"
            conf_dict = self.vol_type_inf[self.conv_dict[self.volume_type1]]
            conf_dict['dist_count'] = 1
            redant.setup_volume(self.volume_name1, self.server_list[0], conf_dict,[self.server_list[0]], self.brick_roots, True)

20) **volume_create_with_custom_bricks**<br>
        This function helps in creating a gluster volume with custom brick configuration.

        Args:
            1. volname(str): volume name that has to be created
            2. node(str): server on which command has to be executed
            3. conf_hash (dict): Config hash providing parameters for volume
                                 creation.
            4. brick_cmd (str): Brick string to use for volume creation
            5. brick_dict (dict): Brick dict containing details of bricks used
                                  to create volume
            6. force (bool): If this option is set to True, then create volume
                             will get executed with force option.
            7. excep (bool): exception flag to bypass the exception if the
                             volume create command fails. If set to False
                             the exception is bypassed and value from remote
                             executioner is returned. Defaults to True

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        Example:
            self.volume_type1 = 'dist'
            self.volume_name1 = f"{self.test_name}-{self.volume_type1}-1"
            conf_dict = self.vol_type_inf[self.conv_dict[self.volume_type1]]
            brick_dict, brick_cmd = redant.form_brick_cmd(self.server_list,
                                                        self.brick_roots,
                                                        self.volume_name1, 4)
            redant.volume_create_with_custom_bricks(self.volume_name1,
                                                    self.server_list[0],
                                                    conf_dict, brick_cmd,
                                                    brick_dict)
            
21) **sanitize_volume**<br>
        This function helps in getting the volume ready for the next test case to be used. Generally, non-disruptive tests will require this function but even some strange scenario can be dealt with this in a test case.

        Args:
            1. volname (str): Name of the volume to be sanitized.
            2. server_list (list) : A list of strings consisting of server IPs.
            3. client_list (list) : A list of strings consisting of client IPs.
            4. brick_root (dict) : The mapping of the brick roots with the
                                   nodes.
            5. vol_param (dict) : Raw recipe for creating volume

        Example:
                vol_param = self.vol_type_inf[self.conv_dict[self.volume_type]]
                self.redant.sanitize_volume(self.vol_name, self.server_list,
                                            self.client_list, self.brick_roots,
                                            vol_param)

22) **cleanup_volume**<br>
        This function comes handy in cleanup operations. Basically, it deletes the volume and its mountpoints.

        Args:
            1. volname (str): Name of the volume to be sanitized.
            2. node (str) : Node on which the commands are run.

        Example:
            self.redant.cleanup_volume(self.volume_name1, self.server_list[0])

 23) **is_distribute_volume**<br>
        This function checks if a volume is a plain distributed volume.
        Args:
            volname (str): Name of the volume.

        Returns:
            bool : True if the volume is distributed volume. False otherwise
            NoneType: None if volume does not exist.
        
        Example:
            self.is_distribute_volume(volname)

24) **wait_for_volume_process_to_be_online**<br>
        This function waits for the volume's processes to be online until timeout

        Args:
            1. volname (str): Name of the volume.
            2. node (str): Node on which commands will be executed.
            3. server_list (list): List of servers

        Optional:
            timeout (int): timeout value in seconds to wait for all volume
                           processes to be online.

        Returns:
            bool: True if the volume's processes are online within timeout,
                  False otherwise
        
        Example:
            self.redant.wait_for_volume_process_to_be_online(self.vol_name,
               self.server_list[0], self.server_list, timeout=600)

25) **get_subvols**
        This function helps in getting the subvolumes in the given volume.

        Args:
            1. volname(str): Volname to get the subvolume for
            2. node(str): Node on which command has to be executed

        Returns:
            list: Empty list if no volumes, or else a list of sub volume
                  lists. Wherein each subvol list contains bricks belonging
                  to that subvol in node:brick_path format.

        Example:
            ret = redant.get_subvols(self.vol_name, self.server_list[0])