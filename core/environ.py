import sys
sys.path.insert(1, ".")
from common.mixin import RedantMixin

class environ:
    """
    Framework level control on the gluster environment. Controlling both
    the setup and the complete cleanup.
    """

    def __init__(self, param_obj, log_path : str, log_level : str):
        """
        Redant mixin obj to be used for server setup and teardown operations
        has to be created.
        """
        self.redant = RedantMixin(param_obj.get_server_config())
        self.redant.init_logger("environ", log_path, log_level)
        self.redant.establish_connection()
        self.server_list = param_obj.get_server_ip_list()

    def setup_env(self):
        """
        Setting up of the environment before the TC execution begins.
        """
        self.redant.start_glusterd()
        self.redant.create_cluster(self.server_list)

    def teardown_env(self):
        """
        The teardown of the complete environment once the test framework
        ends.
        """
        pass
        
