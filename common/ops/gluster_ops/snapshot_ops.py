"""
This file contains one class - SnapshotOps wich holds
operations on the enable, disable the features.uss option,
check for snapd process.
"""
import copy
from common.ops.abstract_ops import AbstractOps


# pylint: disable=assignment-from-none,unsubscriptable-object,not-an-iterable

class SnapshotOps(AbstractOps):
    """
    SnapshotOps class provides APIs to enable, disable
    the features.uss option, check for snapd process.
    """

    def enable_uss(self, volname: str, node: str,
                   excep: bool = True) -> dict:
        """
        Enables uss on the specified volume

        Args:
            volname (str): volume name
            node (str): Node on which cmd has to be executed.
        Optional:
            excep (bool): exception flag to bypass the exception if the
                          enable uss command fails. If set to False
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
        cmd = f"gluster volume set {volname} features.uss enable --mode=script"
        ret = self.execute_abstract_op_node(cmd, node, excep)
        return ret

    def disable_uss(self, volname: str, node: str,
                    excep: bool = True) -> dict:
        """
        Disable uss on the specified volume

        Args:
            volname (str): volume name
            node (str): Node on which cmd has to be executed.
        Optional:
            excep (bool): exception flag to bypass the exception if the
                          disable uss command fails. If set to False
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
        cmd = (f"gluster volume set {volname} features.uss disable"
               " --mode=script")
        ret = self.execute_abstract_op_node(cmd, node, excep)
        return ret

    def is_uss_enabled(self, volname: str, node: str) -> bool:
        """
        Check if uss is Enabled on the specified volume

        Args:
            volname (str): volume name
            node (str): Node on which cmd has to be executed.

        Returns:
            bool : True if successfully enabled uss on the volume.
                   False otherwise.
        """
        option_dict = self.get_volume_options(volname, "uss", node, False)
        if not option_dict:
            self.logger.error(f"USS is not set on the volume {volname}")
            return False

        if ('features.uss' in option_dict
                and option_dict['features.uss'] == 'enable'):
            return True

        return False

    def is_uss_disabled(self, volname: str, node: str) -> bool:
        """
        Check if uss is Disabled on the specified volume

        Args:
            volname (str): volume name
            node (str): Node on which cmd has to be executed.

        Returns:
            bool : True if successfully enabled uss on the volume.
                   False otherwise.
        """
        option_dict = self.get_volume_options(volname, "uss", node, False)
        if not option_dict:
            self.logger.error(f"USS is not set on the volume {volname}")
            return False

        if ('features.uss' in option_dict
                and option_dict['features.uss'] == 'disable'):
            return True

        return False

    def is_snapd_running(self, volname: str, node: str) -> bool:
        """
        Checks if snapd is running on the given node

        Args:
            volname (str): volume name
            node (str): Node on which cmd has to be executed.

        Returns:
            bool: True on success, False otherwise
        """
        vol_status = self.get_volume_status(volname, node)

        if vol_status is None:
            self.logger.error("Failed to get volume status in "
                              "is_snapd_running()")
            return False

        is_enabled = False
        online_status = True
        if 'node' in vol_status[volname]:
            for brick in vol_status[volname]['node']:
                if (brick['hostname'] == "Snapshot Daemon"
                        and brick['path'] == node):
                    is_enabled = True
                    if brick['status'] != '1':
                        online_status = False
                        break

        if not is_enabled:
            self.logger.error("Snapshot Daemon is not enabled for "
                              f"volume {volname}")
            return False
        if not online_status:
            self.logger.error("Snapshot Daemon is not running on node"
                              f" {node}")
            return False
        return True

    def snap_create(self, volname: str, snapname: str, node: str,
                    timestamp: bool = False, description: str = None,
                    force: bool = False, excep: bool = True) -> dict:
        """
        Function for snapshot creation.

        Args:
            volname (str): Name of the volume for which snap is
            is to be created.
            snapname (str): Name of the snapshot.
            node (str): Node wherein this command is to be run.

        Optional:
            timestamp (bool): Whether snap name should contain
            the timestamp or not. Default value being False.
            description (str): Description for snap creation.
            Default value is None.
            force (bool): Whether to create snap by force or not.
            By default it is False.
            excep (bool): Whether to handle exception or not.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        """
        if description is not None:
            description = (f"description \"{description}\"")
        else:
            description = ''

        tstamp = ''
        if not timestamp:
            tstamp = "no-timestamp"

        frce = ''
        if force:
            frce = 'force'

        cmd = (f"gluster snapshot create {snapname} {volname}"
               f" {tstamp} {description} {frce} --mode=script --xml")

        return self.execute_abstract_op_node(cmd, node, excep)

    def snap_clone(self, snapname: str, clonename: str, node: str,
                   excep: bool = True) -> dict:
        """
        Method to clone a snapshot

        Args:
            snapname (str): Name of the snapshot.
            clonename (str): name of the clone.
            node (str): IP address of the node wherein the command
            is to be executed.

        Optional:
            excep (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else
            it isn't.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        """
        cmd = (f"gluster snapshot clone {clonename} {snapname} --mode=script"
               " --xml")
        ret = self.execute_abstract_op_node(cmd, node, excep)
        if not excep and ret['msg']['opRet'] != '0':
            return ret

        # Query the vol info for brick and vol param data.
        brick_data = {}
        ret = self.get_volume_info(node, clonename)
        for brick in ret[clonename]['bricks']:
            ip, brick_path = brick['name'].split(':')
            if ip not in brick_data.keys():
                brick_data[ip] = []
            brick_data[ip].append(brick_path)

        # build the volume params for cloned volume.
        vol_param = {}
        vol_param["dist_count"] = ret[clonename]["distCount"]
        vol_param["replica_count"] = ret[clonename]["replicaCount"]
        vol_param["disperse_count"] = ret[clonename]["disperseCount"]
        vol_param["arbiter_count"] = ret[clonename]["arbiterCount"]
        vol_param["redundancy_count"] = ret[clonename]["redundancyCount"]
        vol_param["transport"] = "tcp"

        # create environ data
        self.es.set_new_volume(clonename, brick_data)
        self.es.set_vol_type(clonename, vol_param)

        return ret

    def snap_restore(self, snapname: str, node: str,
                     excep: bool = True) -> bool:
        """
        Method to restore the snapshot.

        Args:
            snapname (str): Name of the snapshot
            node (str): Node wherien the command is to be executed.

        Optional:
            excep (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else
            it isn't.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        """
        cmd = (f"gluster snapshot restore {snapname} --mode=script --xml")
        return self.execute_abstract_op_node(cmd, node, excep)

    def snap_restore_complete(self, volname: str, snapname: str,
                              node: str, excep: bool = True) -> bool:
        """
        Method restore the snapshot and that is done when volume is stopped.
        Post snap restore, the volume is started again.

        Args:
            volname (str): Name of the volume.
            snpaname (str): name of the snapshot.
            node (str): node wherien the command is to be executed.

        Optional:
            excep (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else
            it isn't.

        Returns:
            bool: True if restore is a success or False.
        """
        # Stop the volume.
        ret = self.volume_stop(volname, node, force=True, excep=excep)
        if not excep and ret['msg']['opRet'] != '0':
            return False

        ret = self.snap_restore(snapname, node, excep)

        if not excep and ret['msg']['opRet'] != '0':
            return False

        # Start the volume
        ret = self.volume_start(volname, node, force=True, excep=excep)
        if not excep and ret['msg']['opRet'] != '0':
            return False

        return True

    def snap_status(self, node, snapname: str = None, volname: str = None,
                    excep: bool = True) -> dict:
        """
        Method for obtaining the snapshot status.

        Args:
            node (str): node wherein the command is to be executed.

        Optional:
            snapname (str): The name of the snapshot
            volname (str): The name of the volume.
            excep (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else
            it isn't.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        """
        if snapname is None and volname is None:
            raise Exception("Provide either snapname or volume name.")
        elif snapname is not None:
            cmd = (f"gluster snapshot status {snapname} --mode=script --xml")
        elif volname is not None:
            cmd = (f"gluster snapshot status volume {volname} --mode=script"
                   " --xml")
        return self.execute_abstract_op_node(cmd, node, excep)

    def get_snap_status(self, node: str, excep: bool = True) -> dict:
        """
        Method to get and parse the snapshot status.

        Args:
            node (str): node wherein the command will be run.

        Optional:
            excep (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else
            it isn't.

        Returns:
            Dict of snapshot statuses parsed and packaged properly and
            in case of excep being false, the raw response.
        """
        cmd = "gluster snapshot status --xml --mode=script"
        ret = self.execute_abstract_op_node(cmd, node)
        ret = ret['msg']['snapStatus']['snapshots']['snapshot']

        if not excep:
            return ret

        if not isinstance(ret, list):
            snap_status = [ret]
        else:
            snap_status = ret
        snap_status_dict = {}
        for snap in snap_status:
            snap_status_dict[snap['name']] = {}
            temp_dict = copy.deepcopy(snap)
            del temp_dict['name']
            snap_status_dict[snap['name']] = temp_dict
        return snap_status_dict

    def get_snap_status_by_snapname(self, snapname: str, node: str,
                                    excep: bool = True) -> dict:
        """
        Method to get a snap status for a specific snapshot.

        Args:
            snapname (str): name of the snapshot
            node (str): node wherein the command is to be executed.

        Optional:
            excep (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else
            it isn't.

        Returns:
            Dictionary of the snap status for the said snapshot or Nonetype
            object.
        """
        snap_status_dict = self.get_snap_status(node, excep)

        if snapname in snap_status_dict.keys():
            return snap_status_dict[snapname]
        return None

    def get_snap_status_by_volname(self, volname: str, node: str,
                                   excep: bool = True) -> dict:
        """
        Method to get a snap status using the volume.

        Args:
            volname (str): Name of the volume
            node (str): node wherein the command is to be executed.

        Optional:
            excep (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else
            it isn't.

        Returns:
            Dictionary of the snap status for the said volume or Nonetype
            object.
        """
        cmd = f"gluster snapshot status volume {volname} --xml --mode=script"
        ret = self.execute_abstract_op_node(cmd, node, excep)
        return ret
        # ret = ret['msg']['snapStatus']['snapshots']['snapshot']

        # if not excep:
        #    return ret

    def snap_info(self, node: str, snapname: str = None, volname: str = None,
                  excep: bool = True) -> dict:
        """
        Method to obtain the snap info.

        Args:
            node (str): Node wherein the command is run.

        Optional:
            snapname (str): name of the snapshot
            volname (str): name of the volume.
            except (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else
            it isn't.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        """
        if snapname is None and volname is None:
            raise Exception("Provide either snapname or volname.")
        elif snapname is not None:
            cmd = (f"gluster snapshot info {snapname} --mode=script --xml")
        elif volname is not None:
            cmd = (
                f"gluster snapshot info volume {volname} --xml --mode=script")
        return self.execute_abstract_op_node(cmd, node, excep)

    def get_snap_info(self, node: str, excep: bool = True) -> dict:
        """
        Method to obtain the snap info command output when run in a node,
        and to access the result by snapnames.

        Args:
            node (str): Node wherein the command is to be run.

        Optional:
            excep (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else
            it isn't.

        Returns:
            ret: A dict in case of valid data or else NoneType value.
        """
        cmd = "gluster snapshot info --xml --mode=script"
        ret = self.execute_abstract_op_node(cmd, node, excep)

        if not excep and ret['msg']['opRet'] != '0':
            return ret

        snap_info_dict = {}
        snap_info = ret['msg']['snapInfo']['snapshots']['snapshot']
        if not isinstance(snap_info, list):
            snap_info_data = [snap_info]
        else:
            snap_info_data = snap_info
        for snap in snap_info_data:
            temp_name = snap['name']
            del snap['name']
            snap_info_dict[temp_name] = copy.deepcopy(snap)
        if snap_info_dict == {}:
            return None
        return snap_info_dict

    def get_snap_info_by_snapname(self, snapname: str, node: str,
                                  excep: bool = True) -> dict:
        """
        Method to obtain the snap info specific to a snapname.

        Args:
            snapname (str): name of the snapshot.
            node (str): the node wherein the command has to be run.

        Optional:
            excep (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else
            it isn't.

        Returns:
            dictionary of the snap info or Nonetype object.
        """
        snap_info_dict = self.get_snap_info(node, excep)

        if snap_info_dict is None:
            return None
        if snapname in snap_info_dict.keys():
            return snap_info_dict[snapname]
        else:
            return None

    def get_snap_info_by_volname(self, volname: str, node: str,
                                 excep: bool = True) -> dict:
        """
        Method to obtain the snap info specific to volume

        Args:
            volname (str): name of the volume.
            node (str): the node wherein the command has to be run.

        Optional:
            excep (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else
            it isn't.

        Returns:
            dictionary of the snap info or Nonetype object.
        """
        snap_info_dict = self.get_snap_info(node, excep)
        if snap_info_dict is None:
            return None

        snap_vol_dict = {}
        for snap in snap_info_dict:
            if snap_info_dict[snap]['snapVolume']['originVolume']['name'] ==\
                    volname:
                temp_dict = copy.deepcopy(snap_info_dict[snap])
                del temp_dict['snapVolume']['originVolume']
                snap_vol_dict[snap] = copy.deepcopy(temp_dict)
        if snap_vol_dict == {}:
            return None
        return snap_vol_dict

    def snap_list(self, node: str, excep: bool = True) -> dict:
        """
        Method to list the snapshots in a node. The response will
        be raw dictionary.

        Args:
            node (str): Node wherein the command will be executed.

        Optional:
            excep (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else
            it isn't.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        """
        cmd = "gluster snapshot list --mode=script --xml"
        return self.execute_abstract_op_node(cmd, node, excep)

    def get_snap_list(self, node: str, volname: str = None,
                      excep: bool = True) -> list:
        """
        Method to return the list of snapshots present.

        Args:
            node (str): Node wherein the command is to be run.

        Optional:
            volname (str): An optional parameter with default value None.
            If provided, the list will be snap list specific to the said
            volume.
            excep (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else
            it isn't.

        Returns:
            ret: A dictionary consisting
               - Flag: To check if the connection failed.
               - msg: message
               - error_msg: error message
               - error_code: error code
               - cmd: command that got executed
               - node: node on which the command got executed.
              when excep is False or else we return list of snapshots.
        """
        if volname is None:
            cmd = "gluster snapshot list --xml --mode=script"
        else:
            cmd = (f"gluster snapshot list {volname} --xml"
                   " --mode=script")

        ret = self.execute_abstract_op_node(cmd, node, excep)

        if not excep:
            return ret

        if not isinstance(ret['msg']['snapList']['snapshot'], list):
            return [ret['msg']['snapList']['snapshot']]
        return ret['msg']['snapList']['snapshot']

    def snap_delete(self, snapname: str, node: str,
                    excep: bool = True) -> dict:
        """
        Method to delete snapshot.

        Args:
            snapname (str): name of the snapshot.
            node (str): Node wherein the command is to be executed.

        Optional:
            excep (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else
            it isn't.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        """
        cmd = (f"gluster snapshot delete {snapname} --xml --mode=script")
        return self.execute_abstract_op_node(cmd, node, excep)

    def snap_delete_by_volumename(self, volname: str, node: str,
                                  excep: bool = True) -> dict:
        """
        Method to delete a snapshot by volumename.

        Args:
            volname (str): name of the volume.
            node (str): Node wherein the command is to be executed.

        Optional:
            excep (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else it
            isn't.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        """
        cmd = (f"gluster snapshot delete volume {volname} --xml --mode=script")
        return self.execute_abstract_op_node(cmd, node, excep)

    def snap_delete_all(self, node: str, excep: bool = True) -> dict:
        """
        Method to delete all snapshots in the cluster.

        Args:
            node (str): Node wherein the command is to be run. This node
            has to be part of the cluster wherein the snapshots are being
            deleted.

        Optional:
            excep (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else it
            isn't.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        """
        # Deleting all snaps.
        cmd = "gluster snapshot delete all --mode=script --xml"
        return self.execute_abstract_op_node(cmd, node, excep)

    def snap_activate(self, snapname: str, node: str, force=False,
                      excep: bool = True) -> dict:
        """
        Method to activate the snapshot.

        Args:
            snapname (str): Name of the snapshot to be activated.
            node (str): Node wherein the command is to be run.

        Optional:
            force (bool): Default value is False.
            excep (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else it
            isn't.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        """
        frce = ''
        if force:
            frce = 'force'

        cmd = (f"gluster snapshot activate {snapname} {frce}"
               " --mode=script --xml")
        return self.execute_abstract_op_node(cmd, node, excep)

    def snap_deactivate(self, snapname: str, node: str,
                        excep: bool = True):
        """
        Method to deactivate a given snaphot.

        Args:
            snapname (str): Name of the snapshot to be activated.
            node (str): Node wherein the command is to be run.

        Optional:
            excep (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else it
            isn't.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        """
        cmd = (f"gluster snapshot deactivate {snapname} --mode=script --xml")
        return self.execute_abstract_op_node(cmd, node, excep)

    def terminate_snapds_on_node(self, node: str) -> dict:
        """
        Method to stop snapd processes on the specified node.

        Args:
            node (str): node wherein the snapd processes have to be stopped
        """
        cmd = "ps aux | grep -v grep | grep snapd | awk '{print $2}'"
        ret = self.execute_abstract_op_node(cmd, node, True)
        snapd_pid = [pid.strip() for pid in ret['msg']]
        for pid in snapd_pid:
            cmd = f"kill -9 {pid}"
            self.execute_abstract_op_node(cmd, node)

    def get_snap_config(self, node: str, volname: str = None,
                        excep: bool = True) -> dict:
        """
        Method to obtain the snapshot config.

        Args:
            node (str): The node wherein the command is executed.

        Optional:
            volname (str): Name of the volume. Default value being None.
            excep (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else it
            isn't.

        Returns:
            Dictionary of config values. Parsing would be done only in case
            of excep being True. Or else, it is left to user to handle the
            output.
        """
        cmd = "gluster snapshot config --mode=script --xml"
        ret = self.execute_abstract_op_node(cmd, node, excep)

        if not excep:
            return ret['msg']

        snap_config = {}
        snap_config['systemConfig'] = ret['msg']['snapConfig']['systemConfig']

        volume_config = []
        temp_vol_conf = ret['msg']['snapConfig']['volumeConfig']['volume']
        if not isinstance(temp_vol_conf, list):
            temp_vol_conf = [temp_vol_conf]

        for vol in temp_vol_conf:
            if volname is not None:
                if volname == vol["name"]:
                    volume_config.append(vol)
            else:
                volume_config.append(vol)
        snap_config['volumeConfig'] = volume_config

        return snap_config

    def set_snap_config(self, option: dict, node: str, volname: str = None,
                        excep: bool = True) -> dict:
        """
        Method to set the snapshot config.

        Args:
            option (dict): Key value pair of the option to be set.
            node (str): Node wherein the command is to be run.
        Optional:
            volname (str): Name of the volume.
            excep (bool): Flag to control exception handling by the
            abstract ops. If True, the exception is handled, or else it
            isn't.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        """
        if volname is None:
            volname = ""

        cmd = (f"gluster snapshot config {volname} {list(option.keys())[0]}"
               f" {list(option.values())[0]} --mode=script --xml")

        return self.execute_abstract_op_node(cmd, node, excep)
