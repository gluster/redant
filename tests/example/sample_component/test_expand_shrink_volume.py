"""
This file contains a test-case which tests
the creation of different volume types.
"""
# nonDisruptive;rep,dist,dist-rep,arb,dist-arb,disp,dist-disp

from tests.nd_parent_test import NdParentTest


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
        force = False
        if self.volume_type == "dist-disp":
            force = True
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots)
        if not ret:
            raise Exception("Failed to expand volume")

        kwargs = {'distribute_count': 1}
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots,
                                   **kwargs)
        if not ret:
            raise Exception("Failed to expand volume")

        redant.get_volume_info(self.server_list[0], self.vol_name)
        redant.get_volume_status(self.vol_name, self.server_list[0])
