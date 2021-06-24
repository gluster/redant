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
        1. Add 100 directories in client mountpoint
        2. Bring one brick offline
        3. Delete those directories
        4. Add another 100 directories in the client
           mountpoint
        5. Bring the brick online
        6. Check the heal info
        7. Check if file attribute exist in heal info
        8. Monitor heal completion
        9. Check if heal is completed
        10. Check heal info for split brain
        11. Check if volume in split brain.
        """
        self._perform_simple_io()
        if self.heal_info is None:
            raise Exception("Failed to get heal info")

        if 'file' not in self.heal_info[0]:
            raise Exception("File not in heal info")
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
