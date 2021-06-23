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
        print("Heal info\n", heal_info)
