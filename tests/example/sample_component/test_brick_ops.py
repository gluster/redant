"""
This test case deals with the following ops:
get_all_bricks_online
get_all_bricks_offline
"""

# disruptive;dist-rep,dist,rep

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
        if not redant.wait_for_glusterd_to_stop(self.server_list[1]):
            # if redant.is_glusterd_running(self.server_list[1]):
            raise Exception(f"Glusterd not stopped on {self.server_list[1]}")

        redant.logger.info(f"Stopped glusterd on {self.server_list[1]}")

        ret = redant.get_online_bricks_list(self.vol_name,
                                            self.server_list[0])
        redant.logger.info(f"Online bricks:{ret}")

        ret = redant.get_offline_bricks_list(self.vol_name,
                                             self.server_list[0])
        redant.logger.info(f"Offline bricks:{ret}")

        redant.start_glusterd(self.server_list[1])

        if not redant.wait_for_glusterd_to_start(self.server_list[1]):
            # if not redant.is_glusterd_running(self.server_list[1]):
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

        redant.volume_start(self.vol_name, self.server_list[0])
        if not redant.wait_for_vol_to_come_online(self.vol_name,
                                                  self.server_list[0]):
            raise Exception(f"Volume {self.vol_name} couldn't be started.")

        # Brick additions
        if self.volume_type != 'dist':
            mul_factor = 3
            _, br_cmd = redant.form_brick_cmd(self.server_list,
                                              self.brick_roots,
                                              self.vol_name, mul_factor, True)
            redant.add_brick(self.vol_name, br_cmd[1:], self.server_list[0],
                             replica_count=3)
        else:
            mul_factor = 1
            _, br_cmd = redant.form_brick_cmd(self.server_list,
                                              self.brick_roots,
                                              self.vol_name, mul_factor, True)
            redant.add_brick(self.vol_name, br_cmd[1:],
                             self.server_list[0])
        redant.es.set_vol_type_param(self.vol_name, 'dist_count', 1)

        # Remove brick operation.
        self.brick_list = redant.get_all_bricks(self.vol_name,
                                                self.server_list[0])
        if self.volume_type != 'dist':
            ret = redant.remove_brick(self.server_list[0], self.vol_name,
                                      self.brick_list[-3:],
                                      'force', 3)
        else:
            ret = redant.remove_brick(self.server_list[0], self.vol_name,
                                      self.brick_list[-1:], 'force')
        redant.es.set_vol_type_param(self.vol_name, 'dist_count', -1)

        self.brick_list = redant.get_all_bricks(self.vol_name,
                                                self.server_list[0])
        if redant.are_bricks_offline(self.vol_name, self.brick_list,
                                     self.server_list[0]):
            raise Exception(f"{self.brick_list} are offline")
