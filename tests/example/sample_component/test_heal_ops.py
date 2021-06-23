"""
Test case that deals with testing the functionalities
in heal ops
"""

# nonDisruptive;rep

from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):

    def run_test(self, redant):
        heal_info = redant.get_heal_info(self.server_list[0],
                                         self.vol_name)
        if heal_info is None:
            raise Exception("Failed to get heal info")
        # monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet finished")
        # is heal complete testing
        if not redant.is_heal_complete(self.server_list[0],
                                       self.vol_name):
            raise Exception("Heal not yet finished")
            