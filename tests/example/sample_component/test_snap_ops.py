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
        2. Getting info and status
        3. Setting a config option
        4. Activating snaps and checking info and status
        5. Mounting the snap
        6. Perform listing inside the snap mount
        7. Unmount the snapshot
        8. Check if the activated snaps are accessible under .snaps
        8. Deactivate the snaps
        9. Check status and info
        10. Disabling the config option
        11. Deletion of snapshot
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
        redant.snap_activate(self.snap_name2, self.server_list[0],
                             force=True)

        redant.snap_clone(self.snap_name, "clone1", self.server_list[0])
        redant.logger.info(redant.snap_list(self.server_list[0]))
        redant.logger.info(redant.get_snap_status(self.server_list[0]))
        snap_running_status = redant.is_snapd_running(self.vol_name,
                                                      self.server_list[0])
        redant.logger.info(f"Snapd run status : {snap_running_status}")

        self.snap_mount = f"/mnt/{self.snap_name}"
        redant.execute_abstract_op_node(f"mkdir {self.snap_mount}",
                                        self.client_list[0])
        redant.mount_snap(self.server_list[0], self.vol_name, self.snap_name,
                          self.client_list[0], self.snap_mount)

        redant.execute_abstract_op_node(f"ls -l {self.snap_mount}",
                                        self.client_list[0])
        redant.unmount_snap(self.snap_name, self.snap_mount,
                            self.client_list[0])

        redant.enable_uss(self.vol_name, self.server_list[0])
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.snap_list = redant.get_snap_list(self.server_list[0],
                                              self.vol_name)
        if not redant.view_snap_from_mount(self.mnt_list,
                                           self.snap_list):
            raise Exception("Snap in .snaps doesn't match snap list provided")

        redant.snap_deactivate(self.snap_name, self.server_list[0])
        redant.snap_deactivate(self.snap_name2, self.server_list[0])
        redant.logger.info(redant.get_snap_status_by_snapname(
            self.snap_name, self.server_list[0]))
        value_set = {"auto-delete": "disable"}
        redant.set_snap_config(value_set, self.server_list[0])
        redant.disable_uss(self.vol_name, self.server_list[0])
        snap_running_status = redant.is_snapd_running(self.vol_name,
                                                      self.server_list[0])
        redant.logger.info(f"Snapd run status : {snap_running_status}")
        redant.snap_delete(self.snap_name, self.server_list[0])
        redant.snap_delete(self.snap_name2, self.server_list[0])
