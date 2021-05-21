# Volume Ops

Volume Ops contains all the functions required to carry out the volume related operations. Given below are all the details about all the functions implemented in the Volume Ops library:

1) [**volume_mount**](https://github.com/srijan-sivakumar/redant/blob/d95bd1a1da8d16131bedf37f8d2ebf8f5c3259f9/common/ops/gluster_ops/volume_ops.py#L16)<br>
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
        volume_mount(self.server_list[0], self.vol_name, self.mountpoint, self.client_list[0])

2) [**volume_unmount**](https://github.com/srijan-sivakumar/redant/blob/d95bd1a1da8d16131bedf37f8d2ebf8f5c3259f9/common/ops/gluster_ops/volume_ops.py#L44)<br>
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

3) [**volume_create**](https://github.com/srijan-sivakumar/redant/blob/d95bd1a1da8d16131bedf37f8d2ebf8f5c3259f9/common/ops/gluster_ops/volume_ops.py#L71)<br>
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

4) [**volume_start**](https://github.com/srijan-sivakumar/redant/blob/d95bd1a1da8d16131bedf37f8d2ebf8f5c3259f9/common/ops/gluster_ops/volume_ops.py#L147)<br>
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

5) [**volume_stop**](https://github.com/srijan-sivakumar/redant/blob/d95bd1a1da8d16131bedf37f8d2ebf8f5c3259f9/common/ops/gluster_ops/volume_ops.py#L180)<br>
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

6) [**volume_delete**](https://github.com/srijan-sivakumar/redant/blob/d95bd1a1da8d16131bedf37f8d2ebf8f5c3259f9/common/ops/gluster_ops/volume_ops.py#L211)<br>
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

7) [**volume_delete_and_brick_cleanup**](https://github.com/srijan-sivakumar/redant/blob/d95bd1a1da8d16131bedf37f8d2ebf8f5c3259f9/common/ops/gluster_ops/volume_ops.py#L236)<br>
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

8) [**get_volume_info**](https://github.com/srijan-sivakumar/redant/blob/d95bd1a1da8d16131bedf37f8d2ebf8f5c3259f9/common/ops/gluster_ops/volume_ops.py#L258)<br>
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

9) [**get_volume_list**](https://github.com/srijan-sivakumar/redant/blob/d95bd1a1da8d16131bedf37f8d2ebf8f5c3259f9/common/ops/gluster_ops/volume_ops.py#L351)<br>
    Fetches the volume names in the gluster.
        Uses xml output of volume list and parses it into to list

        Kwargs:
            node (str): Node on which cmd has to be executed. Deault - None
        Returns:
            list: List of volume names
        Example:
            get_volume_list(server)
            >>>['testvol1', 'testvol2']

10) [**volume_reset**](https://github.com/srijan-sivakumar/redant/blob/d95bd1a1da8d16131bedf37f8d2ebf8f5c3259f9/common/ops/gluster_ops/volume_ops.py#L374)<br>
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

11) [**get_volume_status**](https://github.com/srijan-sivakumar/redant/blob/d95bd1a1da8d16131bedf37f8d2ebf8f5c3259f9/common/ops/gluster_ops/volume_ops.py#L407)<br>
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

12) [**get_volume_options**](https://github.com/srijan-sivakumar/redant/blob/d95bd1a1da8d16131bedf37f8d2ebf8f5c3259f9/common/ops/gluster_ops/volume_ops.py#L494)<br>
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

13) [**set_volume_options**](https://github.com/srijan-sivakumar/redant/blob/d95bd1a1da8d16131bedf37f8d2ebf8f5c3259f9/common/ops/gluster_ops/volume_ops.py#L540)<br>
     Sets the option values for the given volume.

        Args:
            volname (str): volume name
            options (dict): volume options in key value format
        Kwargs:
            node (str): Node on which cmd has to be executed. Default - None
        Example:
            options = {"user.cifs":"enable","user.smb":"enable"}
            set_volume_options("test-vol1", options, self.server_list[0])

14) [**validate_volume_option**](https://github.com/srijan-sivakumar/redant/blob/d95bd1a1da8d16131bedf37f8d2ebf8f5c3259f9/common/ops/gluster_ops/volume_ops.py#L575)<br>
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
            

15) [**reset_volume_option**](https://github.com/srijan-sivakumar/redant/blob/d95bd1a1da8d16131bedf37f8d2ebf8f5c3259f9/common/ops/gluster_ops/volume_ops.py#L592)<br>
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
            

16) [**volume_sync**](https://github.com/srijan-sivakumar/redant/blob/d95bd1a1da8d16131bedf37f8d2ebf8f5c3259f9/common/ops/gluster_ops/volume_ops.py#L629)<br>
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