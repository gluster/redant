"""
This file contains a test case
that checks the add-brick functionality
"""
#disruptive;rep,dist
from tests.parent_test import ParentTest

class TestAddBrick(ParentTest):
    """
    This test class tests the add-brick
    functionality 
    """

    def run_test(self, redant):
        """
        The following steps are undertaken in the testcase:
        1) Peer probed to all the servers
        2) Volume is set up
        3) Bricks are added
        4) Bricks are deleted
        5) Volume is deleted
        6) Peers are detached
        """
        try:
            redant.add_brick(self.vol_name, self.server_list[0],
                                        self.volume_types_info[self.conv_dict[self.volume_type]],
                                        self.server_list, self.brick_roots, True)

        except Exception as error:
            self.TEST_RES = False
            print(f"Test failed:{error}")