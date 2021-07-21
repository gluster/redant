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

Test desciption:
    Testing Volume Type Change from replicated to
    Arbitered volume
"""

# disruptive;rep,dist-rep
# TODO: nfs and cifs to be added

import traceback
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        """
        In case the test fails midway then wait for IO to complete before
        calling the terminate function
        """
        try:
            ret = self.redant.wait_for_io_to_complete(self.io_process,
                                                      self.mounts)
            if not ret:
                raise Exception("IO failed on some of the clients")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _convert_replicated_to_arbiter_volume(self):
        """
        Helper module to convert replicated to arbiter volume.
        """
        # Remove brick to reduce the replica count from replica 3
        ret = self.redant.shrink_volume(self.server_list[0],
                                        self.vol_name,
                                        replica_num=0)
        if not ret:
            raise Exception("Failed to shrink volume")

        # Wait for volume processes to be online
        if not (self.redant.
                wait_for_volume_process_to_be_online(self.vol_name,
                                                     self.server_list[0],
                                                     self.server_list)):
            raise Exception(f"Volume {self.vol_name} process not online "
                            "despite waiting for 300 seconds")

        # Verifying all bricks online
        if not (self.redant.
                verify_all_process_of_volume_are_online(self.vol_name,
                                                        self.server_list[0])):
            raise Exception(f"All volume processes for {self.vol_name}"
                            " are not online")
        # Adding the bricks to make arbiter brick
        replica_arbiter = {'replica_count': 1, 'arbiter_count': 1}
        ret = self.redant.expand_volume(self.server_list[0],
                                        self.vol_name, self.server_list,
                                        self.brick_roots, force=True,
                                        **replica_arbiter)
        if not ret:
            raise Exception(f"Failed to expand the volume  {self.vol_name}")

        # Wait for volume processes to be online
        if not (self.redant.
                wait_for_volume_process_to_be_online(self.vol_name,
                                                     self.server_list[0],
                                                     self.server_list)):
            raise Exception(f"Volume {self.vol_name} process not online "
                            "despite waiting for 300 seconds")

        # Verify volume's all process are online
        if not (self.redant.
                verify_all_process_of_volume_are_online(self.vol_name,
                                                        self.server_list[0])):
            raise Exception(f"All volume processes for {self.vol_name}"
                            " are not online")

    def run_test(self, redant):
        """
        Steps :
        1) Create a replica 3 volume and start volume.
        2) Set client side self heal off.
        3) Fuse mount the volume.
        4) Perform IO
        5) When IO's is running, execute remove-brick command,
           and convert replica 3 to replica 2 volume
        6) Execute add-brick command and convert to arbiter volume,
           provide the path of new arbiter brick.
        7) Issue gluster volume heal.
        8) Heal should be completed with no files in split-brain.
        """

        self.io_process = []
        self.subvols = redant.get_subvols(self.vol_name,
                                          self.server_list[0])

        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        counter = 1

        for mount in self.mounts:
            redant.logger.info(f"Starting IO on {mount['client']}:"
                               f"{mount['mountpath']}")
            proc = redant.create_deep_dirs_with_files(mount['mountpath'],
                                                      counter, 2, 2, 2, 10,
                                                      mount['client'])
            self.io_process.append(proc)
            counter = counter + 10

        # Convert relicated to arbiter volume
        self._convert_replicated_to_arbiter_volume()

        # validate IO
        ret = redant.validate_io_procs(self.io_process,
                                       self.mounts)
        if not ret:
            raise Exception("IO validation failed")

        # Start healing
        if not redant.trigger_heal(self.vol_name,
                                   self.server_list[0]):
            raise Exception("Heal did not trigger")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name,
                                              timeout_period=3600):
            raise Exception("Heal is not yet finished")

        # Check if heal is completed
        if not redant.is_heal_complete(self.server_list[0],
                                       self.vol_name):
            raise Exception("Heal not yet finished")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume is in split-brain")
