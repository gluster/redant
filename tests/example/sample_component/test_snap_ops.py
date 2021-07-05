"""
This file contains a test-case which tests
the snapshot ops.
"""
# disruptive;rep,dist,dist-rep,arb,dist-arb,disp,dist-disp


from tests.d_parent_test import DParentTest


class TestCase(DParentTest):
    """
    Snapshot related testing.
    """

    def run_test(self, redant):
        """
        In the testcase:
        Steps:
        1. Creation of snapshot
        2. Deletion of snapshot
        """
        self.snap_name = f"{self.vol_name}-snap"
        redant.snap_create(self.vol_name, self.snap_name,
                           self.server_list[0])
        redant.logger.info(redant.snap_info(self.server_list[0], volname=self.vol_name))
        redant.logger.info(redant.snap_status(self.server_list[0],
                                               snapname=self.snap_name))
        snap_running_status = redant.is_snapd_running(self.vol_name, self.server_list[0])
        redant.logger.info(f"Snapd run status : {snap_running_status}")
        redant.snap_delete(self.snap_name, self.server_list[0])
