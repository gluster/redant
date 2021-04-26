import traceback
import abc
from common.mixin import RedantMixin
from datetime import datetime


class ParentTest(metaclass=abc.ABCMeta):

    """
    This class contains the standard info and methods which are needed by
    most of the tests

    TEST_RES: states the result of the test case

    """

    conv_dict = {
                    "dist" : "distributed",
                    "rep" : "replicated",
                    "dist-rep" : "distributed-replicated",
                    "disp" : "dispersed",
                    "dist-disp" : "distributed-dispersed",
                    "arb" : "arbiter",
                    "dist-arb" : "distributed-arbiter"
                }
    def __init__(self, mname: str, param_obj, volume_type: str,
                 thread_flag: bool, log_path: str, log_level: str = 'I'):
        """
        Creates volume
        And runs the specific component in the
        test case
        """

        server_details = param_obj.get_server_config()
        client_details = param_obj.get_client_config()

        self.TEST_RES = True
        self.volume_type = volume_type
        self.volume_types_info = param_obj.get_volume_types()
        self._configure(f"{mname}-{volume_type}", server_details,
                        client_details, log_path, log_level)
        self.server_list = param_obj.get_server_ip_list()
        self.client_list = param_obj.get_client_ip_list()
        self.brick_roots = param_obj.get_brick_roots()

        if self.volume_type != "Generic":
            self.vol_name = (f"{mname}-{volume_type}")
            self.redant.volume_create(self.vol_name, self.server_list[0],
                                      self.volume_types_info[self.conv_dict[volume_type]],
                                      self.server_list, self.brick_roots, True)

        if not thread_flag:
            self.redant.start_glusterd()
            self.redant.create_cluster(self.server_list)

    def _configure(self, mname: str, server_details: dict,
                   client_details: dict, log_path: str, log_level: str):
        machine_detail = {**client_details, **server_details}
        self.redant = RedantMixin(machine_detail)
        self.redant.init_logger(mname, log_path, log_level)
        self.redant.establish_connection()
        self.test_name = mname

    @abc.abstractmethod
    def run_test(self):
        pass

    def parent_run_test(self):
        """
        Function to handle the exception logic and invokes the run_test
        which is overridden by every TC.
        """
        self.redant.logger.info(f'''
        ============================================================
        {self.test_name}-{self.volume_type} Started Running: {datetime.now()}
        ============================================================
        ''')
        try:
            self.run_test(self.redant)
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
            self.TEST_RES = False
        self.redant.logger.info(f'''
        ============================================================
        {self.test_name}-{self.volume_type} Finished Running: {datetime.now()}
        ============================================================
        ''')

    def terminate(self):
        """
        Closes connection for now.
        """
        if self.volume_type != 'Generic':
            self.redant.volume_stop(self.vol_name, self.server_list[0], True)
            self.redant.volume_delete(self.vol_name, self.server_list[0])
        self.redant.deconstruct_connection()
