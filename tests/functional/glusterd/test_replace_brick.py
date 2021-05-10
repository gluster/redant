"""
This file contains a test case
that checks the replace-brick functionality
"""
# nonDisruptive;rep,dist-rep,arb,dist-arb
from tests.abstract_test import AbstractTest


class TestReplaceBrick(AbstractTest):
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

            src_brick = (f"{self.server_list[0]}:"
                         f"/glusterfs/brick/"
                         f"{self.vol_name}-0")
            dest_brick = (f"{self.server_list[0]}:"
                          f"/glusterfs/brick/"
                          f"{self.vol_name}-20")

            redant.replace_brick(self.server_list[0], self.vol_name,
                                 src_brick, dest_brick)

        except Exception:
            self.TEST_RES = False
