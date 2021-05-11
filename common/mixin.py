"""
    Module Name:
    Purpose: Refer to the redhat_mixin.md for more information
"""

import copy
from .rexe import Rexe
from .relog import Logger
from .ops.support_ops.io_ops import IoOps
from .ops.gluster_ops.peer_ops import PeerOps
from .ops.gluster_ops.volume_ops import VolumeOps
from .ops.gluster_ops.gluster_ops import GlusterOps
from .ops.gluster_ops.brick_ops import BrickOps


class RedantMixin(GlusterOps, BrickOps, VolumeOps,
                  PeerOps, IoOps, Rexe, Logger):
    """
    A mixin class for redant project to encompass all ops, support
    modules and support for volds which is a volume data structure and
    cleands which is a data structure for node->bricks containing bricks
    which haven't been cleaned up after the volume delete.
    """

    def __init__(self, server_config):
        super().__init__(server_config)
        self.volds = {}
        self.cleands = {}

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
        self.volds[volname] = {"voltype" : {}, "options" : {},
                               "mountpath" : {}, "brickdata" : brickdata,
                               "started" : False}

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
        if node not in self.volds[volname]['mountpath'].keys():
            self.volds[volname]['mountpath'][node] = []
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
        return self.volds[volname]['mountpath']

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
        for (client, mnts) in self.volds[volname]['mountpath'].items():
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
            for (_, mnt_pts) in self.volds[volname]['mountpath'].items():
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
            self.volds[volname]['brickdata'][node].append(brick_dict[node])

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

    def add_data_to_cleands(self, brickdata: dict):
        """
        Method to store the bricks to be cleaned up per node. This
        is to be accessed when the TC ends.
        Arg:
            brickdata (dict) : A dictionary containing keys of node ips
                               and the corresponding values being list of
                               brick paths.
        """
        for node in brickdata:
            if node not in self.cleands.keys():
                self.cleands[node] = []
            self.cleands[node].append(brickdata[node])

    def get_cleands_data(self, node: list=None) -> dict:
        """
        Method to obtain the cleands values pertaining to a node
        or all nodes.
        Arg:
           node (list) : Can be None or list of nodes.
        """
        if node is None:
            return self.cleands
        ret_val = {}
        for n in node:
            if n not in self.cleands.keys():
                raise Exception(f"No data for node {n}")
            ret_val[n] = self.cleands[n]
        return ret_val
