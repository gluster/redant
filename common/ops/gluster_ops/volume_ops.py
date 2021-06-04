"""
This file contains one class - VolumeOps which
holds volume related APIs which will be called
from the test case.
"""
# pylint: disable=too-many-lines

from time import sleep
from collections import OrderedDict
from common.ops.abstract_ops import AbstractOps


class VolumeOps(AbstractOps):
    """
    VolumeOps class provides APIs to perform operations
    related to volumes like mount,create,delete,start,stop,
    fetch information.
    """

    def setup_volume(self, volname: str, node: str, conf_hash: dict,
                     server_list: list, brick_root: list,
                     force: bool = False, create_only: bool = False,
                     excep: bool = True):
        """
        Setup the gluster volume with specified configuration
        Args:
            volname(str): volume name that has to be created
            node(str): server on which command has to be executed
            conf_hash (dict): Config hash providing parameters for volume
                              creation.
            server_list (list): List of servers
            brick_root (list): List of root path of bricks
            force (bool): If this option is set to True, then create volume
                          will get executed with force option.
            create_only (bool): True, if only volume creation is needed.
                                False, will do volume create, start, set
                                operation if any provided in the volume_config
                                By default, value is set to False.
            excep (bool): exception flag to bypass the exception if the
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
        """

        # Check if the volume already exists
        vollist = self.get_volume_list(node)
        if vollist is not None and volname in vollist:
            self.logger.info(f"Volume {volname} already exists.")
            return True

        # Create volume
        ret = self.volume_create(volname, node, conf_hash, server_list,
                                 brick_root, force, excep)
        if create_only:
            return ret

        # Allow sleep before volume start
        sleep(2)

        # Start volume
        ret = self.volume_start(volname, node, excep)
        return ret

    def volume_create(self, volname: str, node: str, conf_hash: dict,
                      server_list: list, brick_root: list,
                      force: bool = False, excep: bool = True):
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
            excep (bool): exception flag to bypass the exception if the
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
        if "replica_count" in conf_hash and conf_hash['replica_count'] > 1:
            # arbiter vol and distributed-arbiter vol
            if "arbiter_count" in conf_hash:
                cmd = (f"gluster volume create {volname} "
                       f"replica {conf_hash['replica_count']} "
                       f"arbiter {conf_hash['arbiter_count']} {brick_cmd} "
                       "--mode=script")
            # replicated vol
            else:
                cmd = (f"gluster volume create {volname} "
                       f"replica {conf_hash['replica_count']}"
                       f" {brick_cmd} --mode=script")
        # dispersed vol and distributed-dispersed vol
        elif "disperse_count" in conf_hash:
            cmd = (f"gluster volume create {volname} disperse {mul_fac} "
                   f"redundancy {conf_hash['redundancy_count']} {brick_cmd} "
                   f"--mode=script")
        # distributed vol
        else:
            cmd = (f"gluster volume create {volname} {brick_cmd} "
                   "--mode=script")
        # TODO: Needs to be changed once CI is mature enough
        force = True
        if force:
            cmd = (f"{cmd} force")

        ret = self.execute_abstract_op_node(cmd, node, excep)

        # Don't add data in case volume creation fails
        if ret['error_code'] == 0:
            self.es.set_new_volume(volname, brick_dict)
            self.es.set_vol_type(volname, conf_hash)

        return ret

    def volume_create_with_custom_bricks(self, volname: str, node: str,
                                         conf_hash: dict, brick_cmd: str,
                                         brick_dict: dict,
                                         force: bool = False,
                                         excep: bool = True):
        """
        Create the gluster volume with custom bricks configuration
        Args:
            volname(str): volume name that has to be created
            node(str): server on which command has to be executed
            conf_hash (dict): Config hash providing parameters for volume
                              creation.
            brick_cmd (str): Brick string to use for volume creation
            brick_dict (dict): Brick dict containing details of bricks used
                               to create volume
            force (bool): If this option is set to True, then create volume
                          will get executed with force option.
            excep (bool): exception flag to bypass the exception if the
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

        """
        if "replica_count" in conf_hash and conf_hash['replica_count'] > 1:
            # arbiter vol and distributed-arbiter vol
            if "arbiter_count" in conf_hash:
                cmd = (f"gluster volume create {volname} "
                       f"replica {conf_hash['replica_count']} "
                       f"arbiter {conf_hash['arbiter_count']} {brick_cmd}"
                       " --mode=script")
            # replicated vol
            else:
                cmd = (f"gluster volume create {volname} "
                       f"replica {conf_hash['replica_count']}"
                       f" {brick_cmd} --mode=script")
        # dispersed vol and distributed-dispersed vol
        elif "disperse_count" in conf_hash:
            cmd = (f"gluster volume create {volname} "
                   f"{conf_hash['disperse_count']} redundancy "
                   f"{conf_hash['redundancy_count']} {brick_cmd}"
                   " --mode=script")
        # distributed vol
        else:
            cmd = (f"gluster volume create {volname} {brick_cmd} "
                   "--mode=script")

        # TODO: Needs to be changed once CI is mature enough
        force = True
        if force:
            cmd = (f"{cmd} force")

        ret = self.execute_abstract_op_node(cmd, node, excep)

        # Don't add data in case volume creation fails
        if ret['error_code'] == 0:
            self.es.set_new_volume(volname, brick_dict)
            self.es.set_vol_type(volname, conf_hash)

        return ret

    def volume_start(self, volname: str, node: str = None,
                     force: bool = False, excep: bool = True):
        """
        Starts the gluster volume
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): Name of the volume to start
            excep (bool): exception flag to bypass the exception if the
                          volume sstart command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True

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

        ret = self.execute_abstract_op_node(cmd, node, excep)

        if ret['msg']['opRet'] == '0':
            self.es.set_volume_start_status(volname, True)

        return ret

    def volume_stop(self, volname: str, node: str = None, force: bool = False,
                    excep: bool = True):
        """
        Stops the gluster volume
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): Name of the volume to stop
            excep (bool): exception flag to bypass the exception if the
                          volume stop command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True
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

        ret = self.execute_abstract_op_node(cmd, node, excep)

        if ret['msg']['opRet'] == '0':
            self.es.set_volume_start_status(volname, False)

        return ret

    def volume_delete(self, volname: str, node: str = None,
                      excep: bool = True):
        """
        Deletes the gluster volume if given volume exists in
        gluster.
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): Name of the volume to delete
            excep (bool): exception flag to bypass the exception if the
                          volume delete command fails. If set to False
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

        """

        cmd = f"gluster volume delete {volname} --mode=script --xml"

        ret = self.execute_abstract_op_node(cmd, node, excep)

        # Delete volume for volds only if the command succeded
        if ret['msg']['opRet'] == '0':
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

        # Perform volume reset.
        self.reset_volume_option(volname, 'all', server_list[0])

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

    def cleanup_volume(self, volname: str, node: str):
        """
        Cleanup volume will delete the volume and its mountpoints.
        Args:
            volname (str): Name of the volume to be sanitized.
            node (str) : Node on which the commands are run.
        """
        # Check if the volume exists.
        if self.es.does_volume_exists(volname):
            # Check if the volume is started.
            if not self.es.get_volume_start_status(volname):
                self.volume_start(volname, node)

            # Check if the volume is mounted on a client.
            if not self.es.get_mnt_pts_dict_in_list(volname) == []:
                # Check if mount dir exists in the node.
                mounts = self.es.get_mnt_pts_dict_in_list(volname)
                for mntd in mounts:
                    mount = mntd['mountpath']
                    # There might be a scenario wherein the mountpoint has
                    # been deleted. Hence stat to check if the mountpoint
                    # even exists. Also, we need to check if the mountpoint
                    # is able to connect to the bricks. There might be a
                    # Transport endpoint error too. But we can just unmount
                    # and remove the values in that scenario.
                    cmd = (f"stat {mount}")
                    ret = self.execute_abstract_op_node(cmd, mntd['client'],
                                                        False)
                    transport_error = "Transport endpoint is not connected"
                    if ret['error_code'] != 0:
                        if transport_error not in ret['error_msg']:
                            continue
                    # One more scenario we have here is when the directory
                    # was unmount but the data structure isn't updated. Hence
                    # the unmout shouldn't be a strict check.
                    self.volume_unmount(volname, mount, mntd['client'], False)
                    self.execute_abstract_op_node(f"rm -rf {mount}",
                                                  mntd['client'])
            self.volume_stop(volname, node, True)
            self.volume_delete(volname, node)

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
                                         'hostUuid': '56d8....'
                                        },
                                        {'name': 'server-vm1:/brick3',
                                         'isArbiter': '0',
                                         '#text': 'server-vm1:/brick3'
                                         'hostUuid': '56d8....'
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
                                         'hostUuid': '56d8....'
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
        if volume_info['count'] == '0':
            return ret_dict
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

    def is_volume_started(self, volname: str, node: str) -> bool:
        """
        Function provides the state of the volume as whether started or stopped
        in boolean.

        Args:
            volname (str): Name of the volume
            node: (str): Node wherein the command is to be executed.

        Returns:
            boolean value. True if started, else False.
        """
        vol_status = self.get_volume_info(node, volname)[volname]['statusStr']
        if vol_status == 'Started':
            return True
        return False

    def wait_for_vol_to_go_offline(self, volname: str, node: str,
                                   timeout: int = 120) -> bool:
        """
        Function to wait till the said volume goes offline.

        Args:
            volname (str): Name of the volume.
            node (str): Node wherein the status will be checked.
            timeout (int): Optional parameter with default value of 120. We
                           will wait for at max 120 seconds before exiting the
                           function.

        Returns:
            True if offline else False.
        """
        itr = 0
        while itr < timeout:
            if not self.is_volume_started(volname, node):
                return True
            itr += 5
            sleep(5)
        return False

    def wait_for_vol_to_come_online(self, volname: str, node: str,
                                    timeout: int = 120) -> bool:
        """
        Function to wait till the said volume comes online.

        Args:
            volname (str): Name of the volume.
            node (str): Node wherein the status will be checked.
            timeout (int): Optional parameter with default value of 120. We
                           will wait for at max 120 seconds before exiting the
                           function.

        Returns:
            True if online else False.
        """
        itr = 0
        while itr < timeout:
            if self.is_volume_started(volname, node):
                return True
            itr += 5
            sleep(5)
        return False

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
                     force: bool = False, excep: bool = True) -> dict:
        """
        Resets the gluster volume of all the reconfigured options.
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): Name of the volume to reset

        Optional:
            force (bool): If this option is set to True, then reset volume
                will get executed with force option. If it is set to False,
                then reset volume will get executed without force option
            excep (bool): exception flag to bypass the exception if the
                          volume reset command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True
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

        ret = self.execute_abstract_op_node(cmd, node, excep)

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
                elif key == 'tasks':
                    nodename = 'task_status'
                    if val is None:
                        ret_dict[volname][nodename] = None
                        continue
                    if not isinstance(val, list):
                        tasks = [val]
                    for task in tasks:
                        if 'task' in list(task.keys()):
                            if nodename not in list(ret_dict[volname].keys()):
                                ret_dict[volname][nodename] = [task['task']]
                            else:
                                ret_dict[volname][nodename].append(
                                    task['task'])
                        else:
                            ret_dict[volname][nodename] = [task]
                else:
                    ret_dict[volname][key] = val

        return ret_dict

    def get_volume_options(self, volname: str = 'all', option: str = 'all',
                           node: str = None, excep: bool = True) -> dict:
        """
        Gets the option values for a given volume.
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
        Kwargs:
            option (str): volume option to get status.
                        If not given, the function returns all the options for
                        the given volume
            excep (bool): exception flag to bypass the exception if the
                          get volume options command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True
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

        cmd = f"gluster volume get {volname} {option} --xml --mode=script"

        ret = self.execute_abstract_op_node(cmd, node, excep)
        if ret['error_code'] != 0:
            return ret
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
                           node: str = None, excep: bool = True):
        """
        Sets the option values for the given volume.
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
            options (dict): volume options in key:value format
            excep (bool): To bypass or not to bypass the exception handling.
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
                self.execute_abstract_op_node(cmd, node, excep)

        for option in volume_options:
            cmd = (f"gluster volume set {volname} {option} "
                   f"{volume_options[option]} --mode=script --xml")

            self.execute_abstract_op_node(cmd, node, excep)
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
                          will get executed with force option. If it is set
                          to False, then reset volume will get executed
                          without force option.
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

    def is_distribute_volume(self, volname: str) -> bool:
        """
        Check if volume is a plain distributed volume

        Args:
            volname (str): Name of the volume.

        Returns:
            bool : True if the volume is distributed volume. False otherwise
            NoneType: None if volume does not exist.
        """
        volume_dict = self.es.get_volume_dict(volname)
        if volume_dict['voltype']['dist_count'] > 0 and\
                volume_dict['voltype']['replica_count'] == 1:
            return True
        return False

    def wait_for_volume_process_to_be_online(self, volname: str, node: str,
                                             server_list: list,
                                             timeout: int = 300) -> bool:
        """
        Waits for the volume's processes to be online until timeout

        Args:
            volname (str): Name of the volume.
            node (str): Node on which commands will be executed.
            server_list (list): List of servers

        Optional:
            timeout (int): timeout value in seconds to wait for all volume
                           processes to be online.

        Returns:
            bool: True if the volume's processes are online within timeout,
                  False otherwise
        """

        # Fetch the brick list of the volume
        brick_list = self.get_all_bricks(volname, node)
        if brick_list is None:
            self.logger.error(f"Failed to get brick list of volume {volname}")
            return False

        # Wait for bricks to be online
        bricks_online_status = (
            self.wait_for_bricks_to_come_online(volname, server_list,
                                                brick_list))
        if not bricks_online_status:
            self.logger.error(f"Failed to wait for the volume {volname} "
                              "processes to be online")
            return False

        # Wait for self-heal-daemons to be online
        self_heal_daemon_online_status = (
            self.wait_for_self_heal_daemons_to_be_online(volname, node,
                                                         timeout))
        if not self_heal_daemon_online_status:
            self.logger.error(f"Failed to wait for the volume {volname}"
                              " processes to be online")
            return False

        # TODO: Add any new process checks here

        self.logger.info(f"Volume {volname} processes are all online")
        return True

    # TODO: Update when we have updated the get_volinfo() to get the subvols
    # def get_subvols(self, volname: str, node: str) -> list:
    #     """
    #     Get the subvolumes in the given volume

    #     Args:
    #         volname(str): Volname to get the subvolume for
    #         node(str): Node on which command has to be executed

    #     Returns:
    #         dict: with empty list values for all keys, if volume doesn't
    #                exist
    #         dict: Dictionary of subvols, value of each key is list of lists
    #               containing subvols
    #     """
    #     subvols = {'volume_subvols': []}

    #     volinfo = self.get_volume_info(node, volname)
    #     if volinfo is not None:
    #         voltype = volinfo[volname]['typeStr']
    #         tmp = volinfo[volname]["bricks"]["brick"]
    #         bricks = [x["name"] for x in tmp if "name" in x]
    #         if voltype == 'Replicate' or voltype == 'Distributed-Replicate':
    #             rep_count = int(volinfo[volname]['replicaCount'])
    #             subvol_list = [bricks[i:i + rep_count]for i in range(0,
    #                                                                  len(bricks),
    #                                                                  rep_count)]
    #             subvols['volume_subvols'] = subvol_list
    #         elif voltype == 'Distribute':
    #             for brick in bricks:
    #                 subvols['volume_subvols'].append([brick])

    #         elif voltype == 'Disperse' or voltype == 'Distributed-Disperse':
    #             disp_count = int(volinfo[volname]['disperseCount'])
    #             subvol_list = ([bricks[i:i + disp_count]
    #                             for i in range(0, len(bricks), disp_count)])
    #             subvols['volume_subvols'] = subvol_list
    #     return subvols
