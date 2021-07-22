"""
Copyright (C) 2015-2020  Red Hat, Inc. <http://www.redhat.com>

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
    Arbiter Test cases related to
    healing in default configuration of the volume
"""

# disruptive;arb,dist-arb
# TODO: nfs, cifs

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Description:
        - set the volume option "data-self-heal-algorithm" to value "full"
        - create IO
        - bring down all bricks processes from selected set
        - modify the data
        - calculate arequal
        - bring bricks online
        - start healing
        - calculate arequal and compare with arequal before bringing bricks
          offline and after bringing bricks online
        """
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        # Setting options
        options = {"data-self-heal-algorithm": "full"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])

        # Creating files on client side
        proc = redant.create_files('1k', self.mountpoint,
                                   self.client_list[0], 100)

        self.all_mounts_procs.append(proc)

        # Validate IO
        if not redant.validate_io_procs(self.all_mounts_procs,
                                        self.mounts):
            raise Exception("IO failed on some of the clients")

        # Select bricks to bring offline
        bricks_to_bring_offline = (redant.
                                   select_volume_bricks_to_bring_offline(
                                       self.vol_name, self.server_list[0]))

        # Bring brick offline
        redant.bring_bricks_offline(self.vol_name,
                                    bricks_to_bring_offline)

        if not redant.are_bricks_offline(self.vol_name,
                                         bricks_to_bring_offline,
                                         self.server_list[0]):
            raise Exception(f'Bricks {bricks_to_bring_offline}'
                            ' are not offline')

        # Modify the data
        self.all_mounts_procs = []

        proc = redant.create_files('1M', self.mountpoint,
                                   self.client_list[0], 100)

        self.all_mounts_procs.append(proc)

        # Validate IO
        if not redant.validate_io_procs(self.all_mounts_procs,
                                        self.mounts):
            raise Exception("IO failed on some of the clients")

        # Get arequal before getting bricks online
        result_before_online = redant.collect_mounts_arequal(self.mounts)

        # Bring brick online
        redant.bring_bricks_online(self.vol_name, self.server_list,
                                   bricks_to_bring_offline)
        if not redant.are_bricks_online(self.vol_name,
                                        bricks_to_bring_offline,
                                        self.server_list[0]):
            raise Exception(f"Bricks {bricks_to_bring_offline}"
                            " are not online.")

        # Wait for volume processes to be online
        if not redant.wait_for_volume_process_to_be_online(self.vol_name,
                                                           self.server_list[0],
                                                           self.server_list):
            raise Exception(f"Failed to wait for volume {self.vol_name} "
                            "processes to be online")

        # Verify volume's all process are online
        if not (redant.
                verify_all_process_of_volume_are_online(self.vol_name,
                                                        self.server_list[0])):
            raise Exception(f"Volume {self.vol_name} : All process"
                            " are not online")

        # Wait for self-heal-daemons to be online
        if not redant.is_shd_daemonized(self.server_list):
            raise Exception("Either No self heal daemon process found")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet finished")

        # is heal complete testing
        if not redant.is_heal_complete(self.server_list[0],
                                       self.vol_name):
            raise Exception("Heal not yet finished")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume in split-brain")

        # # Get arequal after getting bricks online
        result_after_online = redant.collect_mounts_arequal(self.mounts)

        # Checking arequals before bringing bricks online
        # and after bringing bricks online
        if result_after_online != result_before_online:
            raise Exception("Checksums are not equal")
