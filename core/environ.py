import os
import sys
from socket import timeout
import copy
import traceback
import paramiko
from halo import Halo
sys.path.insert(1, ".")
from common.mixin import RedantMixin


class environ:
    """
    Framework level control on the gluster environment. Controlling both
    the setup and the cleanup.
    """

    def __init__(self, param_obj, es, error_handler,
                 log_path: str, log_level: str):
        """
        Redant mixin obj to be used for server setup and teardown operations
        has to be created.
        """
        self.spinner = Halo(spinner='dots')
        self.redant = RedantMixin(param_obj.get_server_config(),
                                  param_obj.get_client_config(), es)
        self.redant.init_logger("environ", log_path, log_level)
        try:
            self.redant.establish_connection()
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            error_handler(e, '''
            It seems one of the nodes is down.
            Message: {exc}.
            Check and run again.
            ''')
        except paramiko.ssh_exception.AuthenticationException as e:
            error_handler(e, """
            Authentication failed.
            Message: {exc}
            Check and run again.
            """)
        except timeout as e:
            error_handler(e, """
            Oops! There was a timeout connecting the servers.
            Message: {exc}
            Check and run again.
            """)
        except Exception as e:
            error_handler(e)

        self.server_list = param_obj.get_server_ip_list()
        self.client_list = param_obj.get_client_ip_list()
        self.brick_root = param_obj.get_brick_roots()

    def get_framework_logger(self):
        """
        To return the framework logger object
        """
        return self.redant.logger

    def _check_and_copy_io_script(self):
        """
        Check if the I/O script exists in the client
        machines. If not transfer it there.
        """
        io_script_dpath = '/tmp/file_dir_ops.py'
        io_script_spath = f'{os.getcwd()}/tools/file_dir_ops.py'
        if not self.redant.path_exists(self.client_list,
                                       [io_script_dpath]):
            for node in self.client_list:
                self.redant.logger.info(f'Copying file_dir_ops to {node}')
                self.redant.transfer_file_from_local(io_script_spath,
                                                     io_script_dpath, node)
        if not self.redant.path_exists(self.server_list,
                                       [io_script_dpath]):
            for node in self.server_list:
                self.redant.logger.info(f'Copying file_dir_ops to {node}')
                self.redant.transfer_file_from_local(io_script_spath,
                                                     io_script_dpath, node)

    def setup_env(self):
        """
        Setting up of the environment before the TC execution begins.
        """
        # invoke the hard reset or hard terminate.
        self.spinner.start("Setting up environment")
        self.redant.hard_terminate(self.server_list, self.client_list,
                                   self.brick_root)
        try:
            self.redant.start_glusterd(self.server_list)
            self.redant.create_cluster(self.server_list)
            self._check_and_copy_io_script()
            self.spinner.succeed("Environment setup successful.")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
            self.spinner.fail("Environment setup failed.")
            sys.exit(0)

    def teardown_env(self):
        """
        The teardown of the complete environment once the test framework
        ends.
        """
        self.spinner.start("Tearing down environment.")
        try:
            self.redant.hard_terminate(self.server_list, self.client_list,
                                       self.brick_root)
            self.spinner.succeed("Tearing down successful.")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
            self.spinner.fail("Environment Teardown failed.")


class FrameworkEnv:
    """
    A class for handling the framework environemnt details. This won't
    affect the environment directly. It is more of a data store.
    """

    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method """
        if FrameworkEnv.__instance is None:
            FrameworkEnv()
        return FrameworkEnv.__instance

    def __init__(self):
        """ vpc """
        if FrameworkEnv.__instance is not None:
            raise Exception("Singleton class can have only one Instance.")
        else:
            FrameworkEnv.__instance = self

    def init_ds(self):
        """
        Method to handle the creation of data structures to store the
        current state of the environment used to run the framework.
        """
        self.volds = {}
        self.clusteropt = {}

    def _validate_volname(self, volname: str):
        """
        A helper function to validate incoming volname parameters if
        its valid.
        Arg:
            volname (str)
        """
        if volname not in self.volds.keys():
            raise Exception(f"No such volume called {volname}")

    def set_new_volume(self, volname: str, brickdata: dict):
        """
        Add a new volume when created to volds.
        Args:
            volname (str)
            brickdata (dict) : dictionary containing objects with key as
                               node ip and values as list of bricks lying
                               under the said node.
        """
        self.volds[volname] = {"started": False, "options": {},
                               "mountpath": {}, "brickdata": brickdata,
                               "voltype": {"dist_count": 0,
                                           "replica_count": 0,
                                           "disperse_count": 0,
                                           "arbiter_count": 0,
                                           "redundancy_count": 0,
                                           "transport": ""}}

    def reset_ds(self):
        """
        Method to reset the DSs.
        """
        self.volds = {}
        self.clusteropt = {}

    def get_volnames(self) -> list:
        """
        Method returns a list of existing volume names
        Returns:
            list : list of volume names
        """
        return list(self.volds.keys())

    def does_volume_exists(self, volname: str) -> bool:
        """
        Method checks if the said volume already exists.
        Arg:
            volname (str)
        Returns:
            True: If volume exists, else False
        """
        if volname in list(self.volds.keys()):
            return True
        return False

    def remove_volume_data(self, volname: str):
        """
        Removing a volume's data from the volds.
        Arg:
            volname (str)
        """
        self._validate_volname(volname)
        del self.volds[volname]

    def get_volume_dict(self, volname: str) -> dict:
        """
        Get the volume dictionary for requested volume.
        Arg:
            volname (str)
        Returns:
            volds dictionary specific to given volume.
        """
        self._validate_volname(volname)
        return self.volds[volname]

    def get_volds(self) -> dict:
        """
        Get the volds.
        Returns:
            volds dictionary as a whole.
        """
        return copy.deepcopy(self.volds)

    def set_vol_type(self, volname: str, voltype_dict: dict):
        """
        Modify volds voltype based on voltype_dict.
        Args:
            volname (str)
            voltype_dict (dict)
        """
        self._validate_volname(volname)
        for (volt_key, volt_val) in list(voltype_dict.items()):
            self.volds[volname]['voltype'][volt_key] = volt_val

    def set_vol_type_param(self, volname: str, voltype_key: str,
                           delta_value: int):
        """
        Method to modify the voltype dictionary in volds.

        Args:
            volname (str)
            voltype_key (str)
            delta_value (int): Change value. Can be positive or negative.
        Returns:
            None
        """
        self._validate_volname(volname)
        if voltype_key not in self.volds[volname]['voltype']:
            self.volds[volname]['voltype'][voltype_key] = 0
        self.volds[volname]['voltype'][voltype_key] += delta_value

    def get_vol_type_param(self, volname: str, voltype_key: str):
        """
        Method to obtain a specific voltype param in volds.

        Args:
            volname (str)
            voltype_key (key)
        Returns:
            The corresponding value and None if the key doesn't exist.
        """
        self._validate_volname(volname)
        if voltype_key not in self.volds[volname]['voltype']:
            return None
        return self.volds[volname]['voltype'][voltype_key]

    def get_vol_type_changes(self, volname: str, pre_voltype: dict) -> dict:
        """
        Method to identify if there are any changes to the volume type
        counts
        Args:
            volname (str)
            pre_voltype (dict)
        Returns:
            True if there are changes, else False.
        """
        self._validate_volname(volname)
        if len(pre_voltype.keys()) !=\
                len(self.volds[volname]['voltype'].keys()):
            return True
        for (pre_voltk, pre_voltv) in list(pre_voltype.items()):
            if pre_voltk == "transport":
                continue
            if pre_voltv != self.volds[volname]['voltype'][pre_voltk]:
                return True
        return False

    def add_new_mountpath(self, volname: str, node: str, path: str):
        """
        Add a new mountpath for given volume and client node.
        Args:
            volname (str)
            node (str) : client node
            path (str) : absolute path of the mountpoint ( or as we call it
                         mountpath :p )
        """
        self._validate_volname(volname)
        if node not in list(self.volds[volname]['mountpath'].keys()):
            self.volds[volname]['mountpath'][node] = []
        if path not in list(self.volds[volname]['mountpath'][node]):
            self.volds[volname]['mountpath'][node].append(path)

    def remove_mountpath(self, volname: str, node: str, path: str):
        """
        Removes the mountpath entries under a client node for a
        given volume.
        Args:
            volname (str)
            node (str) : Client node.
            path (str) : Mountpath
        """
        self._validate_volname(volname)
        if len(self.volds[volname]['mountpath'][node]) == 1:
            del self.volds[volname]['mountpath'][node]
        else:
            self.volds[volname]['mountpath'][node].remove(path)

    def get_mnt_pts_dict(self, volname: str) -> dict:
        """
        Method to obtain the mountpath dictionary.
        Arg:
            volname (str)
        Returns:
            dictionary of nodes and their list of mountpaths.
        """
        self._validate_volname(volname)
        return list(self.volds[volname]['mountpath'])

    def get_mnt_pts_dict_in_list(self, volname: str) -> list:
        """
        Method to return a modified list of mountpath which contains
        multiple client->mountpath relation.
        Args:
            volname (str)
        Returns:
            list of client->mountpath dictionaries.
        """
        self._validate_volname(volname)

        mnt_list = []
        for (client, mnts) in list(self.volds[volname]['mountpath'].items()):
            temp_dict = {}
            for mnt in mnts:
                temp_dict["client"] = client
                temp_dict["mountpath"] = mnt
                copy_dict = copy.deepcopy(temp_dict)
                mnt_list.append(copy_dict)

        return mnt_list

    def get_mnt_pts_list(self, volname: str, node: str = None) -> list:
        """
        Method to obtain the list of mountpaths.
        Args:
            volname (str)
            node (str) client node.
        Returns:
            list of mountpaths belonging to a node or list of
            all mountpoints
        """
        self._validate_volname(volname)
        if node is None:
            mount_point_list = []
            for (_, mnt_pts) in list(self.volds[volname]['mountpath'].items()):
                mount_point_list.append(mnt_pts)
            return mount_point_list
        elif node not in self.volds[volname]['mountpath'].keys():
            raise KeyError
        else:
            return self.volds[volname]['mountpath'][node]

    def add_bricks_to_brickdata(self, volname: str, brick_dict: dict):
        """
        Method to add new set of bricks into the existing brick
        data of a volume.
        Args:
            volname (str)
            brick_dict (dict) : A dictionary with keys of node ip and values
                                being list of bricks under that node.
        """
        self._validate_volname(volname)
        for node in brick_dict:
            if node not in self.volds[volname]['brickdata'].keys():
                self.volds[volname]['brickdata'][node] = []
            self.volds[volname]['brickdata'][node].extend(brick_dict[node])

    def set_brickdata(self, volname: str, brick_dict: dict):
        """
        Method will replace the existing brickdict of a volume with
        whatever user has passed.
        Args:
            volname (str)
            brick_dict (dict) : A dicitonary with keys of node ip and values
                                being list of bricks under that node.
        """
        self._validate_volname(volname)
        self.volds[volname]['brickdata'] = brick_dict

    def remove_bricks_from_brickdata(self, volname: str, brick_data: dict):
        """
        Method to remove the brick brickdata
        """
        self._validate_volname(volname)
        for node in brick_data:
            for brick in brick_data[node]:
                self.volds[volname]["brickdata"][node].remove(brick)

    def get_brickdata(self, volname: str) -> dict:
        """
        Method to obtain brick dictionary
        Args:
            volname (str)
        Return:
            dictionary of nodes and their list of bricks.
        """
        self._validate_volname(volname)
        return self.volds[volname]['brickdata']

    def get_all_bricks_list(self, volname: str) -> list:
        """
        This function creates a list of
        bricks from the brick dictionary

        Args:
            volname: Name of volume
        Returns:
            List of bricks
        """
        brick_dict = self.get_brickdata(volname)
        brick_list = []
        for server in brick_dict:
            for brick in brick_dict[server]:
                brick = f"{server}:{brick}"
                brick_list.append(brick)

        return brick_list

    def get_brick_list(self, volname: str, node: str) -> list:
        """
        Method to obtain brick list
        Args:
            volname (str)
            node (str)
        Returns:
            List of bricks for the given node.
        """
        self._validate_volname(volname)
        if node is None:
            raise ValueError
        if node not in self.volds[volname]['brickdata'].keys():
            raise KeyError
        else:
            return self.volds[volname]['brickdata'][node]

    def set_volume_start_status(self, volname: str, state: bool):
        """
        Method to set the volume start status to true or false.
        Args:
            volname (str)
            state (bool)
        """
        self._validate_volname(volname)
        self.volds[volname]['started'] = state

    def get_volume_start_status(self, volname: str) -> bool:
        """
        Method to get the volume start status.
        Args:
            volname (str)
        Returns:
            bool representing the start state.
        """
        self._validate_volname(volname)
        return self.volds[volname]['started']

    def set_vol_option(self, volname: str, options_dict: dict):
        """
        Method to set a volume option for said volume
        based on the dictionary of options
        Args:
            volname (str)
            option_list (dict) : dict of key value pair of options to be set.
        """
        self._validate_volname(volname)
        if 'options' not in list(self.volds[volname]):
            self.volds[volname]['options'] = {}
        for (opt, opt_val) in list(options_dict.items()):
            self.volds[volname]['options'][opt] = opt_val

    def set_vol_options_all(self, option_dict: dict):
        """
        Method to set a said cluster options.
        Arg:
            option_dict (dict)
        """
        for (key, value) in option_dict.items():
            self.clusteropt[key] = value

    def reset_vol_options_all(self, option_list: list):
        """
        Method to remove a cluster option.
        Args:
            option_list (list)
        """
        for opt in option_list:
            del self.clusteropt[opt]

    def get_vol_option(self, volname: str) -> dict:
        """
        Method to obtain the volume options changed during the TC run.
        Arg:
            volname (str)
        Returns:
            Dictionary
        """
        self._validate_volname(volname)
        return copy.deepcopy(self.volds[volname]['options'])

    def get_vol_options_all(self) -> dict:
        """
        Method to return the cluster options dict.
        Returns:
            dict
        """
        return self.clusteropt

    def is_volume_options_populated(self, volname: str) -> bool:
        """
        Method to reflect if the volume options are
        populated or not.
        Arg:
            volname (str)
        Returns:
            bool
        """
        self._validate_volname(volname)
        if self.volds[volname]['options'] == {}:
            return False
        return True

    def _reset_all_options_in_a_vol(self, volname):
        """
        Method to reset all options of a given volume.
        """
        if self.volds[volname]['options'] != {}:
            for opt in list(self.volds[volname]['options']):
                del self.volds[volname]['options'][opt]

    def reset_volume_option(self, volname: str, option: str):
        """
        Method to handle the reseting of the volume options
        populated inside the volds.
        """
        if volname == "all" and option == "all":
            self.clusteropt = {}
            for vol_name in list(self.volds):
                self._reset_all_options_in_a_vol(vol_name)
        elif volname == "all":
            self.clusteropt = {}
        elif option == "all":
            if self.volds[volname]['options'] != {}:
                for opt in list(self.volds[volname]['options']):
                    del self.volds[volname]['options'][opt]
        elif self.volds[volname]['options'] != {} and \
                option in self.volds[volname]['options']:
            del self.volds[volname]['options'][option]

    def get_volume_nodes(self, volname: str):
        """
        Function to get all the nodes whose bricks are
        part of the volume given
        Args:
            volname (str): volume name whose nodes are to be returned.
        Returns:
            list : list of nodes whose bricks are part of the volume.
        """
        self._validate_volname(volname)
        return list(self.volds[volname]['brickdata'].keys())
