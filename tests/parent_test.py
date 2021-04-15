import traceback
import abc
from support.mixin import RedantMixin
from datetime import datetime

class ParentTest(metaclass=abc.ABCMeta):

    """
    This class contains the standard info and methods which are needed by
    most of the tests

    TEST_RES: states the result of the test case

    """

    def __init__(self, mname: str, config_hashmap: dict, volume_type: str,
                 log_path: str, log_level: str = 'I'):
        """
        Creates volume
        And runs the specific component in the
        test case
        """
        
        server_details = config_hashmap['servers_info']
        client_details = config_hashmap['clients_info']
        volume_types_info = config_hashmap['volume_types']

        self.TEST_RES = True
        self.volume_type = volume_type
        self.server_list = []
        self.client_list = []
        self._configure(mname, server_details, client_details, log_path,
                        log_level)
        self.server_list = list(server_details.keys())
        self.client_list = list(client_details.keys())

        self.redant.start_glusterd(self.server_list)

    def _configure(self, mname: str, server_details: dict,
                   client_details: dict, log_path: str, log_level: str):
        machine_detail = {**client_details , **server_details}
        self.redant = RedantMixin(machine_detail)
        self.redant.init_logger(mname, log_path, log_level)
        self.redant.establish_connection()
        self.test_name = log_path.split('/')[-1:][0][:-4]

    @abc.abstractmethod
    def run_test(self):
        pass

    def parent_run_test(self):
        """
        Function to handle the exception logic and invokes the run_test
        which is overridden by every TC.
        """
        try:
            self.run_test(self.redant)
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(tb)
            self.TEST_RES = False
        self.redant.logger.info(f'''
         ============================================================
                                         
           {self.test_name} finished running: {datetime.now()}       
                                         
         ============================================================
        ''')

    def terminate(self):
        """
        Closes connection for now.
        """
        self.redant.deconstruct_connection()
