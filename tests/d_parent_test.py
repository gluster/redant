import traceback
import abc
from common.mixin import RedantMixin


class DParentTest(metaclass=abc.ABCMeta):

    """
    This class contains the standard info and methods which are needed by
    disruptive testss

    TEST_RES: states the result of the test case

    """

    def __init__(self, mname: str, param_obj, volume_type: str,
                 env_obj, log_path: str, log_level: str = 'I'):
        """
        Creates volume
        And runs the specific component in the
        test case
        """

        server_details = param_obj.get_server_config()
        client_details = param_obj.get_client_config()

        self.TEST_RES = [True]
        self.setup_done = False
        self.volume_type = volume_type
        self.vol_type_inf = param_obj.get_volume_types()
        self.test_name = mname
        self.vol_name = (f"{mname}-{volume_type}")
        self._configure(self.vol_name, server_details, client_details,
                        env_obj, log_path, log_level)
        self.server_list = param_obj.get_server_ip_list()
        self.client_list = param_obj.get_client_ip_list()
        self.brick_roots = param_obj.get_brick_roots()

    def _configure(self, mname: str, server_details: dict,
                   client_details: dict, env_obj, log_path: str,
                   log_level: str):
        self.redant = RedantMixin(server_details, client_details, env_obj,
                                  self.TEST_RES)
        self.redant.init_logger(mname, log_path, log_level)
        self.redant.establish_connection()

    def setup_test(self):
        pass

    @classmethod
    def setup_custom_enable(cls, fun):
        def inner(self, *args, **kwargs):
            self.setup_done = True
            return fun(self, *args, **kwargs)
        return inner

    @abc.abstractmethod
    def run_test(self, redant):
        pass

    def parent_run_test(self):
        """
        Function to handle the exception logic and invokes the run_test
        which is overridden by every TC.
        """
        try:
            self.redant.start_glusterd(self.server_list)
            self.redant.create_cluster(self.server_list)
            self.redant.wait_till_all_peers_connected(self.server_list)

            # Call setup in case you want to override volume creation,
            # start, mounting in the TC
            self.setup_test()

            if not self.setup_done and self.volume_type != "Generic":
                self.redant.setup_volume(self.vol_name, self.server_list[0],
                                         self.vol_type_inf[self.volume_type],
                                         self.server_list, self.brick_roots,
                                         force=True)
                self.mountpoint = (f"/mnt/{self.vol_name}")
                for client in self.client_list:
                    self.redant.execute_abstract_op_node(f"mkdir -p "
                                                         f"{self.mountpoint}",
                                                         client)
                    self.redant.volume_mount(self.server_list[0],
                                             self.vol_name,
                                             self.mountpoint, client)
            self.run_test(self.redant)

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
            if self.TEST_RES[0] is None:
                self.SKIP_REASON = str(error)
            else:
                self.TEST_RES[0] = False

    def terminate(self):
        """
        Closes connection for now.
        """
        # Check if all nodes are up and running.
        for machine in self.server_list + self.client_list:
            ret = self.redant.wait_node_power_up(machine)
            if not ret:
                self.redant.logger.error(f"{machine} is offline.")

        # Validate that glusterd is up and running in the servers.
        self.redant.start_glusterd(self.server_list)
        if not self.redant.wait_for_glusterd_to_start(self.server_list):
            raise Exception("Glusterd start failed.")

        try:
            # Peer probe and validate all peers are in connected state.
            self.redant.peer_probe_servers(self.server_list,
                                           self.server_list[0])
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)

        try:
            for (opt, _) in self.redant.es.get_vol_options_all().items():
                self.redant.reset_volume_option('all', opt,
                                                self.server_list[0])
            self.redant.cleanup_volumes(self.server_list)
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
            self.redant.hard_terminate(self.server_list, self.client_list,
                                       self.brick_roots)
        finally:
            self.redant.deconstruct_connection()
