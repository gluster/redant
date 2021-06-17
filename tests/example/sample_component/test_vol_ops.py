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
        ret = redant.get_subvols(self.vol_name, self.server_list[0])
        redant.logger.info(f"{self.volume_type} : {ret}")
        volname = f"{self.test_name}"
        conf_dict = self.vol_type_inf[self.conv_dict[self.volume_type]]
        ret = redant.bulk_volume_creation(self.server_list[0], 5,
                                          volname, conf_dict,
                                          self.server_list,
                                          self.brick_roots)
