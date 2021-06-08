# Mount Ops

[Heal Ops](../../../common/ops/gluster_ops/mount_ops.py) contains all the functions which are required for mount operations.

1) **volume_mount**<br>

        This function mounts the gluster volume to the client's filesystem.

        Args:
            1. server (str): Hostname or IP address
            2. volname (str): Name of volume to be mounted
            3. path (str): The path of the mount directory (mount point)
            4. node (str): The client node in the cluster where volume
                           mount is to be run
            5. excep (bool): exception flag to bypass the exception if the
                            volume status command fails. If set to False
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
            redant.volume_mount(self.server_list[0], self.vol_name,
                    self.mountpoint, self.client_list[0])

2) **volume_unmount**<br>

        This function unmounts the gluster volume.

        Args:
            1. volname (str): The volume whose mt pt. is to be unmounted.
            2. path (str): The path of the mount directory(mount point)
            3. node (str): The client node in the cluster where volume
                           unmount is to be run
            4. excep (bool): To bypass or not to bypass the exception handling.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        
        Example:
            self.volume_unmount(volname, mount, mntd['client'], False)

3) **is_mounted**<br>
        This function checks if the volume is already mounted or not
        Args:
            1. volname (str): Name of volume to be checked
            2. mpath (str): The path of the mount directory(mount point)
            3. mclient (str): The client node in the cluster where volume
                              is to be mounted
            4. mserver (str): Server to which volume is mounted to
            5. excep (bool): exception flag to bypass the exception if the
                             volume status command fails. If set to False
                             the exception is bypassed and value from remote
                             executioner is returned. Defaults to True
        Returns:
            bool: True if volume is mounted, False otherwise
        
        Example:
            ret = redant.is_mounted(self.vol_name, mount_obj['mountpath'],
                                    mount_obj['client'], self.server_list[0])

4) **get_fuse_process_count**<br>

        This function gets the fuse process count for a given node.

        Args:
            node (str): Node on which fuse process has to be counted.

        Returns:
            int: Number of fuse processes running on the node.
            None: If the command fails to execute.

        Example:
            fuse_proc_count = redant.get_fuse_process_count(server)

5) **wait_for_mountpoint_to_connect**<br>

        This function waits for mountpoint to get connected.
        A failed mountpoint connection results in exception
        'Transport endpoint not connected'. Hence, this functions comes out handy.

        Args:
            mountpoint (str) : the mountpoint to check
            client_node (str): client node to execute the command
            timeout (int) : Timeout by default 20s.

        Returns:
            True if mountpoint gets connected within the timeout
            else False.

        Example:

            ret = redant.wait_for_mountpoint_to_connect(self.mountpoint,
                                                        self.client_list[0])
