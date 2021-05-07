"""
This file contains a test case
that checks the replace-brick functionality
"""
#disruptive;rep
from tests.parent_test import ParentTest

class TestReplaceBrick(ParentTest):
    """
    This test class tests the add-brick
    functionality 
    """

    def run_test(self, redant):
        """
        The following steps are undertaken in the testcase:
        Bricks are replaced
        """
        try:
            redant.add_brick(self.vol_name, self.server_list[0],
                                        self.volume_types_info[self.conv_dict[self.volume_type]],
                                        self.server_list, self.brick_roots, True)
            
            src_brick = f"{self.server_list[0]}:/glusterfs/brick/test_replace_brick-rep-0"
            dest_brick = f"{self.server_list[0]}:/glusterfs/brick/test_replace_brick-rep-9"

            redant.replace_brick(self.server_list[0], self.vol_name, 
                                src_brick, dest_brick)

            redant.remove_brick(self.server_list[0], self.vol_name, 
                                self.volume_types_info[self.conv_dict[self.volume_type]],
                                self.server_list, self.brick_roots, 'force')
            
        except Exception as error:
            self.TEST_RES = False
            print(error)