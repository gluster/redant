"""
This component has a test-case for peers addition and deletion.
"""
#disruptive;dist

from tests.parent_test import ParentTest


class TestCase(ParentTest):
    """
    This TestCase class contains a function to test
    for peer probe , pool list and peer detach.
    """

    def run_test(self):
        self.redant.logger.info("Hello World")
