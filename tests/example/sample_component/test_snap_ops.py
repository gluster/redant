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
        self.snap_name = f"{self.vol_name}-snap1"
        self.snap_name2 = f"{self.vol_name}-snap2"
        redant.snap_create(self.vol_name, self.snap_name,
                           self.server_list[0])
        redant.snap_create(self.vol_name, self.snap_name2,
                           self.server_list[0])

        val = redant.get_snap_config(self.server_list[0], self.vol_name)
        redant.logger.info(f"Snap config : {val}")
        value_set = {"auto-delete": "enable"}
        redant.set_snap_config(value_set, self.server_list[0])
        snap_info = redant.get_snap_info_by_snapname(self.snap_name,
                                                     self.server_list[0])
        redant.logger.info(f"Snap info by snapname {self.snap_name}"
                           f" is {snap_info}")
        redant.enable_uss(self.vol_name, self.server_list[0])
        snap_info = redant.get_snap_info_by_volname(self.vol_name,
                                                    self.server_list[0])
        redant.logger.info(f"Snap info by volname {self.vol_name}"
                           f" is {snap_info}")
        redant.logger.info(redant.snap_status(self.server_list[0],
                                              snapname=self.snap_name))
        snap_running_status = redant.is_snapd_running(self.vol_name,
                                                      self.server_list[0])
        redant.logger.info(f"Snapd run status : {snap_running_status}")
        redant.snap_activate(self.snap_name, self.server_list[0],
                             force=True)
        redant.logger.info(redant.snap_list(self.server_list[0]))
        redant.logger.info(redant.get_snap_status(self.server_list[0]))
        snap_running_status = redant.is_snapd_running(self.vol_name,
                                                      self.server_list[0])
        redant.logger.info(f"Snapd run status : {snap_running_status}")
        redant.snap_deactivate(self.snap_name, self.server_list[0])
        redant.logger.info(redant.get_snap_status_by_snapname(
            self.snap_name, self.server_list[0]))
        redant.disable_uss(self.vol_name, self.server_list[0])
        snap_running_status = redant.is_snapd_running(self.vol_name,
                                                      self.server_list[0])
        redant.logger.info(f"Snapd run status : {snap_running_status}")
        redant.snap_delete(self.snap_name, self.server_list[0])
        redant.snap_delete(self.snap_name2, self.server_list[0])
