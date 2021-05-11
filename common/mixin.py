"""
    Module Name:
    Purpose: Refer to the redhat_mixin.md for more information
"""

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
    A mixin class for redant project to encompass all ops and support
    modules.
    """

    def __init__(self, server_config):
        super().__init__(server_config)
        self.volds = {}

    def get_mnt_pts_dict(self, volname: str) -> dict:
        """
        Method to obtain the mountpath dictionary.
        Arg:
            volname (str)
        Returns:
            dictionary of nodes and their list of mountpaths.
        """
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
        if volname is None:
            raise Exception("Volname not provided.")

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
        if node is None:
            mount_point_list = []
            for (_, mnt_pts) in self.volds[volname]['mountpath'].items():
                mount_point_list.append(mnt_pts)
            return mount_point_list
        elif node not in self.volds[volname]['mountpath'].keys():
            raise KeyError
        else:
            return self.volds[volname]['mountpath'][node]

    def get_brick_dict(self, volname: str) -> dict:
        """
        Method to obtain brick dictionary
        Args:
            volname (str)
        Return:
            dictionary of nodes and their list of bricks.
        """
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
        if node is None:
            raise ValueError
        if node not in self.volds[volname]['brickdata'].keys():
            raise KeyError
        else:
            return self.volds[volname]['brickdata'][node]
