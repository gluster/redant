from redant_libs.redant_mixin import RedantMixin as rm


class Parent_Test:

    """
    This class contains the standard info and methods which are needed by
    most of the tests

    PASS: states the pass value

    TEST_RES: states the result of the test case

    COMPONENT: component which is to be tested
    TEST_NAME: name of the test to run
    """

    PASS: bool

    TEST_RES: bool

    COMPONENT: str
    TEST_NAME: str

    def __init__(self, passed: bool, component: str, test_name: str):
        """
        Creates volume
        And runs the specific component in the
        test case
        """
        self.PASS = passed
        self.TEST_RES = self.PASS
        self.COMPONENT = component
        self. TEST_NAME = test_name
        rm.rlog(f"{self.TEST_NAME} from {self.COMPONENT} inits")

    def init(self):
        pass

    def run_test(self):
        pass

    def terminate(self):
        """
        Closes connection for now.
        """
        rm.rlog(f"{self.TEST_NAME} terminates")
