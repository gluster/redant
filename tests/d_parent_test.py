import traceback
import abc
from common.mixin import RedantMixin


class DParentTest(metaclass=abc.ABCMeta):

    """
    This class contains the standard info and methods which are needed by
    disruptive testss

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
        Creates volume
        And runs the specific component in the
        test case
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
        machine_detail = {**client_details, **server_details}
        self.redant = RedantMixin(machine_detail, env_obj)
        self.redant.init_logger(mname, log_path, log_level)
        self.redant.establish_connection()
        self.test_name = mname

    @abc.abstractmethod
    def run_test(self, redant):
        pass

    def parent_run_test(self):
        """
        Function to handle the exception logic and invokes the run_test
        which is overridden by every TC.
        """
        try:
            self.redant.start_glusterd()
            self.redant.create_cluster(self.server_list)

            if self.volume_type != "Generic":
                self.vol_name = (f"{self.test_name}-{self.volume_type}")
                self.redant.volume_create(
                    self.vol_name, self.server_list[0],
                    self.vol_type_inf[self.conv_dict[self.volume_type]],
                    self.server_list, self.brick_roots, True)
                self.redant.volume_start(self.vol_name, self.server_list[0])
                self.mountpoint = (f"/mnt/{self.vol_name}")
                self.redant.execute_abstract_op_node(f"mkdir -p "
                                                     f"{self.mountpoint}",
                                                     self.client_list[0])
                self.redant.volume_mount(self.server_list[0], self.vol_name,
                                         self.mountpoint, self.client_list[0])
            self.run_test(self.redant)

            if self.volume_type != 'Generic':
                self.redant.volume_unmount(self.vol_name, self.mountpoint,
                                           self.client_list[0])
                self.redant.execute_abstract_op_node(f"rm -rf "
                                                     f"{self.mountpoint}",
                                                     self.client_list[0])
                self.redant.volume_stop(
                    self.vol_name, self.server_list[0], True)
                self.redant.volume_delete(self.vol_name, self.server_list[0])
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
