"""
    Module Name:
    Purpose: Refer to the redhat_mixin.md for more information
"""
from redant_libs.support_libs.rexe import Rexe
from redant_libs.support_libs.relog import Logger
from redant_libs.gluster_libs.peer_ops import peer_ops
from redant_libs.gluster_libs.volume_ops import VolumeOps


# pylint: disable=W0107
class RedantMixin(peer_ops, VolumeOps, Rexe, Logger):
    """
    A mixin class for redant project to encompass all ops and support
    modules.
    """
    pass
