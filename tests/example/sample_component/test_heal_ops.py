"""
Test case that deals with testing the functionalities
in heal ops
"""

# nonDisruptive;rep

from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):

    def _perform_simple_io(self):
        cmd = (f"mkdir {self.mountpoint}/test"
               "{1..100}.txt")
        self.redant.execute_abstract_op_node(cmd,
                                             self.client_list[0])
        bricks_list = self.redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])
        self.redant.bring_bricks_offline(self.vol_name,
                                         bricks_list[2])
        cmd = f"rm -rf {self.mountpoint}/test*"
        self.redant.execute_abstract_op_node(cmd,
                                             self.client_list[0])
        cmd = (f"mkdir {self.mountpoint}/test"
               "{101..200}.txt")
        self.redant.execute_abstract_op_node(cmd,
                                             self.client_list[0])
        self.redant.bring_bricks_online(self.vol_name,
                                        self.server_list,
                                        bricks_list[2])
        self.heal_info = self.redant.get_heal_info(self.server_list[0],
                                                   self.vol_name)

    def run_test(self, redant):
        """
        * Trigger full heal
        * Bring self heal daemon process offline
        * Enable granular heal
        * Disable granular heal
        * Disable self heal daemon
        * Re-enable self heal daemon
        * Add 100 directories in client mountpoint
        * Bring one brick offline
        * Delete those directories
        * Add another 100 directories in the client
        * mountpoint
        * Bring the brick online
        * Check the heal info
        * Check if file attribute exist in heal info
        * Check is shd is daemonized
        * Check if shd daemon is running
        * Get the heal info summary
        * Monitor heal completion
        * Check if heal is completed
        * Check heal info for split brain
        * Check if volume in split brain.
        """
        redant.trigger_heal_full(self.vol_name, self.server_list[0])
        redant.bring_self_heal_daemon_process_offline(self.server_list)

        if not redant.enable_granular_heal(self.vol_name,
                                           self.server_list[0]):
            raise Exception("Failed to enable granular-entry-heal")

        if not redant.disable_granular_heal(self.vol_name,
                                            self.server_list[0]):
            raise Exception("Failed to disable granular-entry-heal")

        if not (redant.
                disable_self_heal_daemon(self.vol_name,
                                         self.server_list[0])):
            raise Exception("Failed to disable the self-heal daemon")
        if not (redant.
                enable_self_heal_daemon(self.vol_name,
                                        self.server_list[0])):
            raise Exception("Failed to enable the self-heal daemon")

        self._perform_simple_io()
        if self.heal_info is None:
            raise Exception("Failed to get heal info")

        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        if not (redant.
                do_bricks_exist_in_shd_volfile(self.vol_name,
                                               bricks_list,
                                               self.server_list[0])):
            raise Exception("Bricks do not exist in shd volfile")
        if 'file' not in self.heal_info[0]:
            raise Exception("File not in heal info")

        if not redant.is_shd_daemonized(self.server_list):
            raise Exception("Self heal daemon not daemonized")

        if not redant.is_shd_daemon_running(self.server_list[0],
                                            self.server_list[1],
                                            self.vol_name):
            raise Exception("Self-heal Daemon not running on"
                            f" node {self.server_list[1]}")

        heal_summ = redant.get_heal_info_summary(self.server_list[0],
                                                 self.vol_name)
        if heal_summ is None:
            raise Exception("Unable to get the heal info summary")

        # monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet finished")

        # is heal complete testing
        if not redant.is_heal_complete(self.server_list[0],
                                       self.vol_name):
            raise Exception("Heal not yet finished")

        sp_br_heal_info = (redant.
                           get_heal_info_split_brain(self.server_list[0],
                                                     self.vol_name))
        if sp_br_heal_info is None:
            raise Exception("Failed to get heal info in split-brain")

        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume in split-brain")
