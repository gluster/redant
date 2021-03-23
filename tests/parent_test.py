from redant_libs.redant_mixin import RedantMixin

class ParentTest:

    """
    This class contains the standard info and methods which are needed by
    most of the tests

    TEST_RES: states the result of the test case

    """

    def __init__(self, client_list: list, server_list: list, log_path: str, log_level: str = 'I'):
        """
        Creates volume
        And runs the specific component in the
        test case
        """
        
        self.TEST_RES = True
        self.client_list = client_list
        self.server_list = server_list
        self._configure(log_path, log_level)

    def _configure(self, log_path: str, log_level: str):
        machines = self.client_list + self.server_list
        self.redant = RedantMixin(machines)
        self.redant.set_logging_options(log_path, log_level)
        self.redant.establish_connection()


    def run_test(self):
        pass

    def terminate(self):
        """
        Closes connection for now.
        """
        pass
