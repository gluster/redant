from redant_libs.redant_mixin import RedantMixin

class ParentTest:

    """
    This class contains the standard info and methods which are needed by
    most of the tests

    TEST_RES: states the result of the test case

    """

    def __init__(self, mname: str, client_details: list, server_details: list,
                 volume_type: str, log_path: str, log_level: str = 'I'):
        """
        Creates volume
        And runs the specific component in the
        test case
        """
        
        self.TEST_RES = True
        self.volume_type = volume_type
        self.server_list = []
        self.client_list = []
        self._configure(mname, server_details, client_details, log_path,
                        log_level)
        for server in server_details:
            self.server_list.append(server["hostname"])
        for client in client_details:
            self.client_list.append(client["hostname"])

    def _configure(self, mname: str, server_details: dict,
                   client_details: dict, log_path: str, log_level: str):
        machine_detail = self.client_details + self.server_details
        self.redant = RedantMixin(machine_detail)
        self.redant.init_logger(mname, log_path, log_level)
        self.redant.establish_connection()


    def run_test(self):
        pass

    def terminate(self):
        """
        Closes connection for now.
        """
        pass
