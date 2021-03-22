
class ParentTest:

    """
    This class contains the standard info and methods which are needed by
    most of the tests

    PASS: states the pass value

    TEST_RES: states the result of the test case

    """

    def __init__(self, redant: object):
        """
        Creates volume
        And runs the specific component in the
        test case
        """
        self.PASS = True
        self.redant = redant
        self.TEST_RES = self.PASS

    def run_test(self):
        pass

    def terminate(self):
        """
        Closes connection for now.
        """
