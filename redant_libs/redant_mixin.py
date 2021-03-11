from redant_libs.support_libs.rexe import Rexe
from redant_libs.support_libs.relog import Logger
from redant_libs.gluster_libs.peer_ops import peer_ops

class redant_mixin(Rexe, Logger, peer_ops):
    pass
