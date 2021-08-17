"""
  Copyright (C) 2017-2020  Red Hat, Inc. <http://www.redhat.com>

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along
  with this program; if not, write to the Free Software Foundation, Inc.,
  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

Description:
        Test cases in this module tests whether heal command for resolving
        split-brains will resolve all the files in data-split brains by using
        one of the method (bigger-file/latest-mtime/source-brick).
"""

# disruptive;rep

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create
        """
        conf_hash = self.vol_type_inf['rep']
        conf_hash['replica_count'] = 2
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots, force=True)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node(f"mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            self.redant.volume_mount(self.server_list[0],
                                     self.vol_name,
                                     self.mountpoint, client)

    def _verify_brick_arequals(self):
        """
        Collects arequal for all bricks and compare
        """
        all_bricks = (self.redant.get_online_bricks_list(
                      self.vol_name, self.server_list[0]))
        arequal = self.redant.collect_bricks_arequal(all_bricks)
        if len(set(tuple(x) for x in arequal)) != 1:
            raise Exception("Arequal is not same on all the bricks "
                            "in the subvol")

    def run_test(self, redant):
        # Setting options
        options = {"metadata-self-heal": "off",
                   "entry-self-heal": "off",
                   "data-self-heal": "off"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])

        redant.logger.info(f"mount point = {self.mountpoint}")

        # Creating files and directories on client side
        cmd = (f"for i in `seq 1 10`; do mkdir {self.mountpoint}/dir_$i; "
               "for j in `seq 1 5`; do dd if=/dev/urandom "
               f"of={self.mountpoint}/dir_$i/file_$j bs=1K count=1; "
               f"done; dd if=/dev/urandom of={self.mountpoint}/file_$i "
               "bs=1K count=1; done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Check arequals for all the bricks
        self._verify_brick_arequals()

        # Set option self-heal-daemon to OFF
        options = {"self-heal-daemon": "off"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])

        # Bring brick1 offline
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])

        redant.bring_bricks_offline(self.vol_name, bricks_list[0])
        if not redant.are_bricks_offline(self.vol_name, bricks_list[0],
                                         self.server_list[0]):
            raise Exception(f"Brick {bricks_list[0]} is not offline")

        # Modify the contents of the files
        cmd = ("for i in `seq 1 10`; do for j in `seq 1 5`;"
               "do dd if=/dev/urandom "
               f"of={self.mountpoint}/dir_$i/file_$j bs=1M count=1;"
               "done; dd if=/dev/urandom "
               f"of={self.mountpoint}/file_$i bs=1K count=1; done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Bring brick1 online and check the status
        redant.bring_bricks_online(self.vol_name, self.server_list,
                                   bricks_list[0])
        if not redant.are_bricks_online(self.vol_name, bricks_list[0],
                                        self.server_list[0]):
            raise Exception(f"Brick {bricks_list[0]} is not online")

        # Bring brick2 offline
        redant.bring_bricks_offline(self.vol_name, bricks_list[1])
        if not redant.are_bricks_offline(self.vol_name, bricks_list[1],
                                         self.server_list[1]):
            raise Exception(f"Brick {bricks_list[1]} is not offline")

        # Modify the contents of the files
        cmd = ("for i in `seq 1 10`; do for j in `seq 1 5`;"
               "do dd if=/dev/urandom "
               f"of={self.mountpoint}/dir_$i/file_$j bs=1M count=2;"
               "done; dd if=/dev/urandom "
               f"of={self.mountpoint}/file_$i bs=1K count=2; done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Bring brick2 online and check the status
        redant.bring_bricks_online(self.vol_name, self.server_list,
                                   bricks_list[1])
        if not redant.are_bricks_online(self.vol_name, bricks_list[1],
                                        self.server_list[1]):
            raise Exception(f"Brick {bricks_list[1]} is not online")

        # Set option self-heal-daemon to ON
        options = {"self-heal-daemon": "on"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # Check if there any files in split-brain
        if not redant.is_volume_in_split_brain(self.server_list[0],
                                               self.vol_name):
            raise Exception("Failed to create split-brain state")

        node, _ = bricks_list[1].split(':')
        cmd = ("gluster v heal " + self.vol_name + " split-brain "
               "source-brick " + bricks_list[1])
        redant.execute_abstract_op_node(cmd, node)

        # triggering heal
        if not redant.trigger_heal(self.vol_name,
                                   self.server_list[0]):
            raise Exception("Start heal failed")

        # waiting for heal to complete
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name,
                                              timeout_period=120):
            raise Exception("Heal not yet completed")

        # Try accessing the file content from the mount
        cmd = ("for i in `seq 1 10`; "
               f"do cat {self.mountpoint}/file_$i > /dev/null;"
               "for j in `seq 1 5` ; "
               f"do cat {self.mountpoint}/dir_$i/file_$j > /dev/null;"
               "done ; done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # checking if file is in split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume is in split-brain state")

        # Check arequals for all the bricks
        self._verify_brick_arequals()
