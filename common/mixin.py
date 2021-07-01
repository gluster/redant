"""
    Module Name:
    Purpose: Refer to the redhat_mixin.md for more information
"""

from .rexe import Rexe
from .relog import Logger
from .ops.support_ops.io_ops import IoOps
from .ops.support_ops.machine_ops import MachineOps
from .ops.gluster_ops.peer_ops import PeerOps
from .ops.gluster_ops.volume_ops import VolumeOps
from .ops.gluster_ops.gluster_ops import GlusterOps
from .ops.gluster_ops.brick_ops import BrickOps
from .ops.gluster_ops.profile_ops import ProfileOps
from .ops.gluster_ops.rebalance_ops import RebalanceOps
from .ops.gluster_ops.mount_ops import MountOps
from .ops.gluster_ops.heal_ops import HealOps
from .ops.gluster_ops.shared_storage_ops import SharedStorageOps
from .ops.gluster_ops.bitrot_ops import BitrotOps
from .ops.gluster_ops.auth_ops import AuthOps
from .ops.gluster_ops.snapshot_ops import SnapshotOps


class RedantMixin(GlusterOps, VolumeOps, BrickOps, PeerOps,
                  IoOps, MachineOps, MountOps, ProfileOps, RebalanceOps,
                  HealOps, SharedStorageOps, AuthOps, BitrotOps, SnapshotOps,
                  Rexe, Logger):
    """
    A mixin class for redant project to encompass all ops, support
    modules and encapsulates the object responsible for the framework
    level data structure for volume and cleanup.
    """

    def __init__(self, server_config, client_config, es):
        super().__init__(server_config, client_config)
        self.es = es
