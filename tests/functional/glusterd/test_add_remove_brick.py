"""
This file contains a test case
that checks the add-brick functionality
"""
#disruptive;rep,dist,arb
from tests.parent_test import ParentTest

class TestAddBrick(ParentTest):
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
        try:
            redant.add_brick(self.vol_name, self.server_list[0],
                                        self.volume_types_info[self.conv_dict[self.volume_type]],
                                        self.server_list, self.brick_roots, True)
            redant.add_brick(self.vol_name, self.server_list[0],
                                        self.volume_types_info[self.conv_dict[self.volume_type]],
                                        self.server_list, self.brick_roots, True)
            redant.remove_brick(self.server_list[0], self.vol_name, 
                                self.volume_types_info[self.conv_dict[self.volume_type]],
                                self.server_list, self.brick_roots, 'force')
            
        except Exception as error:
            self.TEST_RES = False