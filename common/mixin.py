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
from .ops.gluster_ops.profile_ops import ProfileOps


class RedantMixin(GlusterOps, BrickOps, VolumeOps, PeerOps,
                  IoOps, ProfileOps, Rexe, Logger):
    """
    A mixin class for redant project to encompass all ops, support
    modules and encapsulates the object responsible for the framework
    level data structure for volume and cleanup.
    """

    def __init__(self, server_config, es):
        super().__init__(server_config)
        self.es = es
