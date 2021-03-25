"""
    Module Name:
    Purpose: Refer to the redhat_mixin.md for more information
"""
from ops.support_ops.rexe import Rexe
from ops.support_ops.relog import Logger
from ops.support_ops.io_ops import io_ops
from ops.gluster_ops.peer_ops import peer_ops
from ops.gluster_ops.volume_ops import VolumeOps
from ops.gluster_ops.gluster_ops import GlusterOps


# pylint: disable=W0107
class RedantMixin(GlusterOps, VolumeOps, peer_ops, io_ops, Rexe, Logger):
    """
    A mixin class for redant project to encompass all ops and support
    modules.
    """
    pass
