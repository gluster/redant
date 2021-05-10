"""
    Module Name:
    Purpose: Refer to the redhat_mixin.md for more information
"""
from rexe import Rexe
from relog import Logger
from ops.support_ops.io_ops import IoOps
from ops.gluster_ops.peer_ops import PeerOps
from ops.gluster_ops.volume_ops import VolumeOps
from ops.gluster_ops.gluster_ops import GlusterOps


class RedantMixin(GlusterOps, VolumeOps, PeerOps, IoOps, Rexe, Logger):
    """
    A mixin class for redant project to encompass all ops and support
    modules.
    """

    def __init__(self, server_config):
        super(RedantMixin, self).__init__(server_config)
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

    def get_mnt_pts_list(self, volname: str, node: str = None) -> list:
        """
        Method to obtain the list of mountpaths.
        Args:
            volname (str)
            node (str) client node.
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

    def get_brick_dict(self, volname: str, node: str = None) -> dict:
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
        Returns:
            List of bricks for the given node.
        """
        if node not in self.volds[volname]['brickdata'].keys():
            raise KeyError
        else:
            return self.volds[volname]['brickdata'][node]
