"""
This file contains one class - VolumeOps which
holds volume related APIs which will be called
from the test case.
"""
from collections import OrderedDict
from common.ops.abstract_ops import AbstractOps


class VolumeOps(AbstractOps):
    """
    VolumeOps class provides APIs to perform operations
    related to volumes like mount,create,delete,start,stop,
    fetch information.
    """

    def volume_mount(self, server: str, volname: str,
                     path: str, node: str = None):
        """
        Mounts the gluster volume to the client's filesystem.
        Args:
            node (str): The client node in the cluster where volume
                        mount is to be run
            server (str): Hostname or IP address
            volname (str): Name of volume to be mounted
            path (str): The path of the mount directory(mount point)

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        """

        cmd = f"mount -t glusterfs {server}:/{volname} {path}"

        ret = self.execute_abstract_op_node(cmd, node)
        self.es.add_new_mountpath(volname, node, path)
        return ret

    def volume_unmount(self, volname: str, path: str, node: str = None):
        """
        Unmounts the gluster volume .
        Args:
            volname (str): The volume whose mt pt. is to be unmounted.
            node (str): The client node in the cluster where volume
                        unmount is to be run
            server (str): Hostname or IP address
            path (str): The path of the mount directory(mount point)

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        """

        cmd = f"umount {path}"

        ret = self.execute_abstract_op_node(cmd, node)
        self.es.remove_mountpath(volname, node, path)
        return ret

    def volume_create(self, volname: str, node: str, conf_hash: dict,
                      server_list: list, brick_root: list,
                      force: bool = False):
        """
        Create the gluster volume with specified configuration
        Args:
            volname(str): volume name that has to be created
            node(str): server on which command has to be executed
            conf_hash (dict): Config hash providing parameters for volume
            creation.
            server_list (list): List of servers
            brick_root (list): List of root path of bricks
            force (bool): If this option is set to True, then create volume
            will get executed with force option.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        """
        brick_cmd = ""
        mul_fac = 0
        cmd = ""
        brick_dict = {}
        if "replica_count" in conf_hash:
            mul_fac = conf_hash["replica_count"]

            if "arbiter_count" in conf_hash:
                mul_fac += conf_hash["arbiter_count"]

            if "dist_count" in conf_hash:
                mul_fac *= conf_hash["dist_count"]

        elif "dist_count" in conf_hash:
            mul_fac = conf_hash["dist_count"]

            if "disperse_count" in conf_hash:
                mul_fac *= conf_hash["disperse_count"]

        else:
            mul_fac = conf_hash["disperse_count"]

        brick_dict, brick_cmd = self.form_brick_cmd(server_list, brick_root,
                                                    volname, mul_fac)
        if "replica_count" in conf_hash:
            # arbiter vol and distributed-arbiter vol
            if "arbiter_count" in conf_hash:
                cmd = (f"gluster volume create {volname} "
                       f"replica {conf_hash['replica_count']} "
                       f"arbiter {conf_hash['arbiter_count']}{brick_cmd}")
            # replicated vol
            else:
                cmd = (f"gluster volume create {volname} "
                       f"replica {conf_hash['replica_count']}"
                       f"{brick_cmd}")
        # dispersed vol and distributed-dispersed vol
        elif "disperse_count" in conf_hash:
            cmd = (f"gluster volume create {volname} disperse {mul_fac} "
                   f"redundancy {conf_hash['redundancy_count']}{brick_cmd} "
                   f"--mode=script")
        # distributed vol
        else:
            cmd = (f"gluster volume create {volname}{brick_cmd}")
        if force:
            cmd = (f"{cmd} force")

        ret = self.execute_abstract_op_node(cmd, node)
        self.es.set_new_volume(volname, brick_dict)

        return ret

    def volume_start(self, volname: str, node: str = None,
                     force: bool = False):
        """
        Starts the gluster volume
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): Name of the volume to start

        Kwargs:
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

        """

        if force:
            cmd = f"gluster volume start {volname} force --mode=script --xml"
        else:
            cmd = f"gluster volume start {volname} --mode=script --xml"

        ret = self.execute_abstract_op_node(cmd, node)
        self.es.set_volume_start_status(volname, True)

        return ret

    def volume_stop(self, volname: str, node: str = None, force: bool = False):
        """
        Stops the gluster volume
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): Name of the volume to stop
        Kwargs:
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

        """

        if force:
            cmd = f"gluster volume stop {volname} force --mode=script --xml"
        else:
            cmd = f"gluster volume stop {volname} --mode=script --xml"

        ret = self.execute_abstract_op_node(cmd, node)
        self.es.set_volume_start_status(volname, False)

        return ret

    def volume_delete(self, volname: str, node: str = None):
        """
        Deletes the gluster volume if given volume exists in
        gluster.
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): Name of the volume to delete
        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        """

        cmd = f"gluster volume delete {volname} --mode=script --xml"

        ret = self.execute_abstract_op_node(cmd, node)
        self.es.add_data_to_cleands(self.es.get_brickdata(volname))
        self.es.remove_volume_data(volname)
        return ret

    def sanitize_volume(self, volname: str, server_list: list,
                        client_list: list, brick_root: dict, vol_param: dict):
        """
        Sanitizing of the volume will be getting the volume
        ready for the next test case to be used (ND tests)
        or even within a test case for maybe some untold
        and strange scenario.
        Args:
            volname (str): Name of the volume to be sanitized.
            server_list (list) : A list of strings consisting of server IPs.
            client_list (list) : A list of strings consisting of client IPs.
            brick_root (dict) : The mapping of the brick roots with the
                                nodes.
            vol_param (dict) : Raw recipe for creating volume
        """
        # Check if the volume exists.
        if not self.es.does_volume_exists(volname):
            # A test case is for sure doing what it isn't supposed to..
            # But the framework here takes the higher ground and handles
            # things for the betterment of all TCs.
            self.volume_create(volname, server_list[0], vol_param,
                               server_list, brick_root, True)

        # Check if the volume is started.
        if not self.es.get_volume_start_status(volname):
            self.volume_start(volname, server_list[0])

        # Check if the volume is mounted on a client.
        if self.es.get_mnt_pts_dict_in_list(volname) == []:
            # Check if mount dir exists in the node.
            mountdir = f"/mnt/{volname}"
            for node in client_list:
                self.execute_abstract_op_node(f"umount {mountdir}", node)
                self.execute_abstract_op_node(f"mkdir -p {mountdir}", node)
                self.volume_mount(server_list[0], volname, mountdir, node)

        # Clear out the mountpoint data.
        mount_list = self.es.get_mnt_pts_dict_in_list(volname)
        for mntd in mount_list:
            self.execute_abstract_op_node(f"rm -rf {mntd['mountpath']}/*",
                                          mntd['client'])

    def cleanup_volume(self, volname: str, server_list: list):
        """
        Sanitizing of the volume will be getting the volume
        ready for the next test case to be used (ND tests)
        or even within a test case for maybe some untold
        and strange scenario.
        Args:
            volname (str): Name of the volume to be sanitized.
            server_list (list) : A list of strings consisting of server IPs.
        """
        # Check if the volume exists.
        if self.es.does_volume_exists(volname):
            # Check if the volume is started.
            if not self.es.get_volume_start_status(volname):
                self.volume_start(volname, server_list[0])

            # Check if the volume is mounted on a client.
            if not self.es.get_mnt_pts_dict_in_list(volname) == []:
                # Check if mount dir exists in the node.
                mounts = self.es.get_mnt_pts_dict_in_list(volname)
                for mntd in mounts:
                    mount = mntd['mountpath']
                    self.volume_unmount(volname, mount, mntd['client'])
                    self.execute_abstract_op_node(f"rm -rf {mount}",
                                                  mntd['client'])
            self.volume_stop(volname, server_list[0], True)
            self.volume_delete(volname, server_list[0])

    def get_volume_info(self, node: str = None, volname: str = 'all') -> dict:
        """
        Gives volume information
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
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

        """

        cmd = f"gluster volume info {volname} --xml"

        ret = self.execute_abstract_op_node(cmd, node)

        volume_info = ret['msg']['volInfo']['volumes']
        ret_dict = {}
        volume_list = volume_info['volume']
        if not isinstance(volume_list, list):
            volume_list = [volume_list]
        for volume in volume_list:
            for key, val in volume.items():
                if key == 'name':
                    volname = val
                    ret_dict[volname] = {}
                elif key == 'bricks':
                    ret_dict[volname]['bricks'] = []
                    brick_list = val['brick']
                    if not isinstance(brick_list, list):
                        brick_list = [brick_list]
                    for brick in brick_list:
                        brick_info = {}
                        for b_key, b_val in brick.items():
                            brick_info[b_key] = b_val
                        ret_dict[volname]['bricks'].append(brick_info)
                elif key == 'options':
                    ret_dict[volname]['options'] = {}
                    for option in val['option']:
                        for opt, opt_val in option.items():
                            if opt == 'name':
                                opt_name = opt_val
                            elif opt == 'value':
                                opt_value = opt_val
                        ret_dict[volname]['options'][opt_name] = opt_value
                else:
                    ret_dict[volname][key] = val

        return ret_dict

    def get_volume_list(self, node: str = None) -> list:
        """
        Fetches the volume names in the gluster.
        Uses xml output of volume list and parses it into to list
        Args:
            node (str): Node on which cmd has to be executed.
        Returns:
            list: List of volume names
        Example:
            get_volume_list(server)
            >>>['testvol1', 'testvol2']
        """
        cmd = "gluster volume list --xml"

        ret = self.execute_abstract_op_node(cmd, node)

        volume_list_count = int(ret['msg']['volList']['count'])
        volume_list = []
        if volume_list_count != 0:
            volume_list = ret['msg']['volList']['volume']

        return volume_list

    def volume_reset(self, volname: str, node: str = None,
                     force: bool = False):
        """
        Resets the gluster volume of all the reconfigured options.
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): Name of the volume to reset
        Kwargs:
            force (bool): If this option is set to True, then reset volume
                will get executed with force option. If it is set to False,
                then reset volume will get executed without force option
        Example:
            volume_reset("testvol",server)

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        """
        if force:
            cmd = f"gluster volume reset {volname} force --mode=script --xml"
        else:
            cmd = f"gluster volume reset {volname} --mode=script --xml"

        ret = self.execute_abstract_op_node(cmd, node)

        return ret

    def get_volume_status(self, volname: str = 'all', node: str = None,
                          service: str = '', options: str = '',
                          excep: bool = True) -> dict:
        """
        Gets the status of all or the specified volume
        Args:
            node (str): Node on which cmd has to be executed.
        Kwargs:
            volname (str): volume name. Defaults to 'all'
            service (str): name of the service to get status.
                service can be, [nfs|shd|<BRICK>|quotad]], If not given,
                the function returns all the services
            options (str): options can be,
                [detail|clients|mem|inode|fd|callpool|tasks]. If not given,
                the function returns the output of gluster volume status
            excep (bool): exception flag to bypass the exception if the
                          volume status command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True

        Returns:
            dict: volume status in dict of dictionary format
            None: In case no volumes are present
        Example:
            get_volume_status("test-vol1",server)
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
        """
        ret = {}

        cmd = f"gluster volume status {volname} {service} {options} --xml"
        if not excep:
            ret = self.execute_abstract_op_node(cmd, node, excep=False)

            if ret['error_code'] != 0:
                self.logger.error(ret['error_msg'])
                return ret
            elif isinstance(ret['msg'], (OrderedDict, dict)):
                if int(ret['msg']['opRet']) != 0:
                    self.logger.error(ret['msg']['opErrstr'])
                    return ret
        else:
            ret = self.execute_abstract_op_node(cmd, node)

        volume_status = ret['msg']['volStatus']['volumes']

        if volume_status is None:
            return None

        ret_dict = {}
        volume_list = volume_status['volume']
        if not isinstance(volume_list, list):
            volume_list = [volume_list]
        for volume in volume_list:
            for key, val in volume.items():
                if key == 'volName':
                    volname = val
                    ret_dict[volname] = {}
                elif key == 'node':
                    ret_dict[volname]['node'] = []
                    node_list = val
                    if not isinstance(node_list, list):
                        node_list = [node_list]
                    for node_i in node_list:
                        node_info = {}
                        for n_key, n_val in node_i.items():
                            if n_key == 'ports':
                                port_info = {}
                                for p_key, p_val in n_val.items():
                                    port_info[p_key] = p_val
                                node_info[n_key] = port_info
                            else:
                                node_info[n_key] = n_val
                        ret_dict[volname]['node'].append(node_info)
                else:
                    ret_dict[volname][key] = val

        return ret_dict

    def get_volume_options(self, volname: str = 'all', option: str = 'all',
                           node: str = None) -> dict:
        """
        Gets the option values for a given volume.
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
        Kwargs:
            option (str): volume option to get status.
                        If not given, the function returns all the options for
                        the given volume
        Returns:
            dict: value for the given volume option in dict format, on success
            NoneType: on failure
        Example:
            get_volume_options(server)
         >>>{ 'cluster.server-quorum-ratio': '51 (DEFAULT)',
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
        """

        cmd = f"gluster volume get {volname} {option} --mode=script --xml"

        ret = self.execute_abstract_op_node(cmd, node)

        volume_options = ret['msg']['volGetopts']

        ret_dict = {}
        option_list = volume_options['Opt']
        if not isinstance(option_list, list):
            option_list = [option_list]
        for option_i in option_list:
            option_name = option_i['Option']
            option_value = option_i['Value']
            ret_dict[option_name] = option_value

        return ret_dict

    def set_volume_options(self, volname: str, options: dict,
                           node: str = None):
        """
        Sets the option values for the given volume.
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
            options (dict): volume options in key
                value format
        Example:
            options = {"user.cifs":"enable","user.smb":"enable"}
            set_volume_options("test-vol1", options, server)
        """

        volume_options = options
        if 'group' in volume_options:
            group_options = volume_options.pop('group')
            if not isinstance(group_options, list):
                group_options = [group_options]
            for group_option in group_options:
                cmd = (f"gluster volume set {volname} group {group_option} "
                       "--mode=script --xml")
                self.execute_abstract_op_node(cmd, node)

        for option in volume_options:
            cmd = (f"gluster volume set {volname} {option} "
                   f"{volume_options[option]} --mode=script --xml")

            self.execute_abstract_op_node(cmd, node)
            if volname != 'all':
                self.es.set_vol_option(volname,
                                       {option: volume_options[option]})
            else:
                self.es.set_vol_options_all({option: volume_options[option]})

    def validate_volume_option(self, volname: str, options: dict,
                               node: str = None):
        """
        Validate the volume options
        Args:
            node (str) : Node on which cmd has to be executed
            volname (str) : volume name
            option (dict) : dictionary of options which are to be validated.
        Returns:
            No value if success or else ValueError will be raised.
        """
        for (opt, val) in options.items():
            ret_val = self.get_volume_options(volname, opt, node)
            if ret_val[opt] != val:
                raise Exception(f"Option {opt} has value {ret_val[opt]}"
                                f" not {val}")

    def reset_volume_option(self, volname: str, option: str,
                            node: str = None, force: bool = False):
        """
        Resets the volume option
        Args:
            node (str): Node on which cmd has to be executed
            volname (str): volume name
            option (str): volume option
        Kwargs:
            force (bool): If this option is set to True, then reset volume
                will get executed with force option. If it is set to False,
                then reset volume will get executed without force option
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

        """

        if force:
            cmd = (f"gluster volume reset {volname} {option} force"
                   "--mode=script --xml")
        else:
            cmd = f"gluster vol reset {volname} {option} --mode=script --xml"

        ret = self.execute_abstract_op_node(cmd, node)
        self.es.reset_volume_option(volname, option)

        return ret

    def volume_sync(self, hostname: str, node: str, volname: str = 'all'):
        """
        Sync the volume to the specified host
        Args:
            node (str): Node on which cmd has to be executed.
            hostname (str): host name to which volume has to be sync'ed
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

        """

        cmd = f"gluster volume sync {hostname} {volname} --mode=script --xml"

        ret = self.execute_abstract_op_node(cmd, node)

        return ret
