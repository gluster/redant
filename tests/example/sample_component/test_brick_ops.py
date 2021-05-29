"""
This test case deals with the following ops:
get_all_bricks_online
get_all_bricks_offline
"""

# disruptive;dist-rep

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        1. Get online bricks list
        2. Stop glusterd on one node
        3. Get online bricks list
        4. Get offline bricks list
        5. Restart glusterd on that node
        6. Get online bricks list
        7. Get offline bricks list
        8. Stop the volume
        9. Get online bricks list
        10. Get offline bricks list
        """
        ret = redant.get_online_bricks_list(self.vol_name,
                                            self.server_list[0])
        redant.logger.info(f"Online bricks:{ret}")

        brick_list = ret[0:1]
        ret = redant.bring_bricks_offline(self.vol_name, brick_list)
        if not ret:
            raise Exception(f"{brick_list} still online.")

        ret = redant.get_online_bricks_list(self.vol_name,
                                            self.server_list[0])
        redant.logger.info(f"Online bricks:{ret}")

        ret = redant.bring_bricks_online(self.vol_name, self.server_list,
                                         brick_list)
        if not ret:
            raise Exception(f"{brick_list} still offline.")

        redant.stop_glusterd(self.server_list[1])
        redant.wait_for_glusterd_to_stop(self.server_list[1])
        if redant.is_glusterd_running(self.server_list[1]):
            raise Exception(f"Glusterd not stopped on {self.server_list[1]}")

        redant.logger.info(f"Stopped glusterd on {self.server_list[1]}")

        ret = redant.get_online_bricks_list(self.vol_name,
                                            self.server_list[0])
        redant.logger.info(f"Online bricks:{ret}")

        ret = redant.get_offline_bricks_list(self.vol_name,
                                             self.server_list[0])
        redant.logger.info(f"Offline bricks:{ret}")

        redant.start_glusterd(self.server_list[1])

        redant.wait_for_glusterd_to_start(self.server_list[1])
        if not redant.is_glusterd_running(self.server_list[1]):
            raise Exception(f"Glusterd not started on {self.server_list[1]}")

        redant.logger.info(f"Started glusterd on {self.server_list[1]}")
        ret = redant.get_online_bricks_list(self.vol_name,
                                            self.server_list[0])
        redant.logger.info(f"Online bricks:{ret}")

        ret = redant.get_offline_bricks_list(self.vol_name,
                                             self.server_list[0])
        redant.logger.info(f"Offline bricks:{ret}")

        redant.volume_stop(self.vol_name, self.server_list[0])
        redant.logger.info(f"Stopped volume {self.vol_name}")

        ret = redant.get_online_bricks_list(self.vol_name,
                                            self.server_list[0])
        redant.logger.info(f"Online bricks:{ret}")

        ret = redant.get_offline_bricks_list(self.vol_name,
                                             self.server_list[0])
        redant.logger.info(f"Offline bricks:{ret}")
