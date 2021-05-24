import traceback
import abc
from common.mixin import RedantMixin


class LazyParentTest(metaclass=abc.ABCMeta):

    """
    This class is a lazy parent, responsible for
    providing abstractions for volume_create and
    volume_destroy.

    TEST_RES: states the result of the test case
    """

    conv_dict = {
        "dist": "distributed",
        "rep": "replicated",
        "dist-rep": "distributed-replicated",
                    "disp": "dispersed",
                    "dist-disp": "distributed-dispersed",
                    "arb": "arbiter",
                    "dist-arb": "distributed-arbiter"
    }

    def __init__(self, mname: str, param_obj, volume_type: str,
                 env_obj, log_path: str, log_level: str = 'I'):
        """
        Lazy parent will only initialize the connection.
        """

        server_details = param_obj.get_server_config()
        client_details = param_obj.get_client_config()

        self.TEST_RES = True
        self.volume_type = volume_type
        self.vol_type_inf = param_obj.get_volume_types()
        self._configure(f"{mname}-{volume_type}", server_details,
                        client_details, env_obj, log_path, log_level)
        self.server_list = param_obj.get_server_ip_list()
        self.client_list = param_obj.get_client_ip_list()
        self.brick_roots = param_obj.get_brick_roots()

    def _configure(self, mname: str, server_details: dict,
                   client_details: dict, env_obj, log_path: str,
                   log_level: str):
        self.redant = RedantMixin(server_details, client_details, env_obj)
        self.redant.init_logger(mname, log_path, log_level)
        self.redant.establish_connection()
        self.test_name = mname

    @abc.abstractmethod
    def run_test(self, redant):
        pass

    def parent_run_test(self):
        """
        Function to handle the exception logic and invokes the run_test
        which is overridden by by child test.
        """
        try:
            self.vol_name = (f"redant-{self.volume_type}")
            self.mountpoint = (f"/mnt/redant-{self.volume_type}")
            self.run_test(self.redant)
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
            self.TEST_RES = False

    def terminate(self):
        """
        Closes connection for now.
        """
        self.redant.deconstruct_connection()
