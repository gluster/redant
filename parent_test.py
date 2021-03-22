# from redant_libs.redant_mixin import RedantMixin as rm


class ParentTest:

    """
    This class contains the standard info and methods which are needed by
    most of the tests

    PASS: states the pass value

    TEST_RES: states the result of the test case

    COMPONENT: component which is to be tested
    TEST_NAME: name of the test to run
    """

    def __init__(self, passed: bool):
        """
        Creates volume
        And runs the specific component in the
        test case
        """
        self.PASS = passed
        self.TEST_RES = self.PASS

    def run_test(self):
        pass

    def terminate(self):
        """
        Closes connection for now.
        """
