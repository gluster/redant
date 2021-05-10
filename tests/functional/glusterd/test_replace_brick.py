"""
This file contains a test case
that checks the replace-brick functionality
"""
# disruptive;rep
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
            vol_dict = self.conv_dict[self.volume_type]
            redant.add_brick(self.vol_name, self.server_list[0],
                             self.vol_type_inf[vol_dict],
                             self.server_list, self.brick_roots, True)

            src_brick = (f"{self.server_list[0]}:"
                         f"/glusterfs/brick/"
                         f"test_replace_brick-rep-0")
            dest_brick = (f"{self.server_list[0]}:"
                          f"/glusterfs/brick/"
                          f"test_replace_brick-rep-9")

            redant.replace_brick(self.server_list[0], self.vol_name,
                                 src_brick, dest_brick)

            redant.remove_brick(self.server_list[0], self.vol_name,
                                self.vol_type_inf[vol_dict],
                                self.server_list, self.brick_roots, 'force')

        except Exception:
            self.TEST_RES = False
