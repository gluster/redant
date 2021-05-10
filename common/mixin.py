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
