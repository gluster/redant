"""
This file contains a test-case which tests
the creation of different volume types.
"""
# nonDisruptive;rep,dist,dist-rep,arb,dist-arb,disp,dist-disp

from tests.abstract_test import AbstractTest


class TestCase(NdParentTest):
    """
    The test case contains one function to test
    for the creation of different types of files and
    some operations on it.
    """

    def run_test(self, redant):
        """
        In the testcase:
        """
