import sys
sys.path.insert(1, ".")
from common.mixin import RedantMixin

class environ:
    """
    Framework level control on the gluster environment. Controlling both
    the setup and the complete cleanup.
    """

    def __init__(self, config_hashm : dict, log_path : str, log_level : str):
        """
        Redant mixin obj to be used for server setup and teardown operations
        has to be created.
        """
        self.server_details = config_hashm['servers_info']
        machine_details = {**self.server_details}
        self.redant = RedantMixin(machine_details)
        self.redant.init_logger("environ", log_path, log_level)
        self.redant.establish_connection()

    def setup_env(self):
        """
        Setting up of the environment before the TC execution begins.
        """
        self.redant.start_glusterd()
        self.redant.create_cluster(list(self.server_details.keys()))

    def teardown_env(self):
        """
        The teardown of the complete environment once the test framework
        ends.
        """
        pass
        
