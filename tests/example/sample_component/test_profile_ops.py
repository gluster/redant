"""
This file contains a test-case which tests
the profile operations on a volume
"""

from tests.nd_parent_test import NdParentTest


# nonDisruptive;dist
class TestCase(NdParentTest):

    def run_test(self, redant):
        """
        Steps:
        1) Profile start
        2) Profile info
        3) Profile stop
        """

        redant.profile_start(self.vol_name, self.server_list[0])
        profile_options = ['peek', 'incremental', 'clear',
                           'incremental peek', 'cumulative']
        for opt in profile_options:
            redant.profile_info(self.vol_name, opt, self.server_list[0])
        redant.profile_stop(self.vol_name, self.server_list[0])
