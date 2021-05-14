"""
This file contains a test case
that checks the add-brick and remove-brick functionality
"""
# nonDisruptive;dist-rep,rep,dist,arb
from tests.abstract_test import AbstractTest


class TestAddBrick(AbstractTest):
    """
    This test class tests the add-brick
    functionality
    """

    def run_test(self, redant):
        """
        The following steps are undertaken in the testcase:
        Bricks are added
        Bricks are removed
        """
        vol_dict = self.conv_dict[self.volume_type]
        redant.add_brick(self.vol_name, self.server_list[0],
                         self.vol_type_inf[vol_dict],
                         self.server_list, self.brick_roots, True)

        redant.remove_brick(self.server_list[0], self.vol_name,
                            self.vol_type_inf[vol_dict],
                            self.server_list, self.brick_roots, 'force')
