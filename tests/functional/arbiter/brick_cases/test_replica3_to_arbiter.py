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
@runs_on([['replicated', 'distributed-replicated'],
          ['glusterfs', 'nfs', 'cifs']])
"""

# disruptive;rep
# TODO: nfs and cifs to be added

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    # def _wait_for_untar_completion(self):
    #     """Wait for untar to complete"""
    #     has_process_stopped = []
    #     for proc in self.io_process:
    #         try:
    #             ret, _, _ = proc.async_communicate()
    #             if not ret:
    #                 has_process_stopped.append(False)
    #             has_process_stopped.append(True)
    #         except ValueError:
    #             has_process_stopped.append(True)
    #     return all(has_process_stopped)

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
        Description: Replica 3 to arbiter conversion with ongoing IO's

        Steps :
        1) Create a replica 3 volume and start volume.
        2) Set client side self heal off.
        3) Fuse mount the volume.
        4) Create directory dir1 and write data.
           Example: untar linux tar from the client into the dir1
        5) When IO's is running, execute remove-brick command,
           and convert replica 3 to replica 2 volume
        6) Execute add-brick command and convert to arbiter volume,
           provide the path of new arbiter brick.
        7) Issue gluster volume heal.
        8) Heal should be completed with no files in split-brain.
        """

        # pylint: disable=too-many-statements
        self.subvols = redant.get_subvols(self.vol_name,
                                          self.server_list[0])
        self._convert_replicated_to_arbiter_volume()
        # # Create a dir to start untar
        # self.linux_untar_dir = "{}/{}".format(self.mounts[0].mountpoint,
        #                                       "linuxuntar")
        # ret = mkdir(self.clients[0], self.linux_untar_dir)
        # self.assertTrue(ret, "Failed to create dir linuxuntar for untar")

        # # Start linux untar on dir linuxuntar
        # self.io_process = run_linux_untar(self.clients[0],
        #                                   self.mounts[0].mountpoint,
        #                                   dirs=tuple(['linuxuntar']))
        # self.is_io_running = True

        # # Convert relicated to arbiter volume
        # self._convert_replicated_to_arbiter_volume()

        # # Wait for IO to complete.
        # ret = self._wait_for_untar_completion()
        # self.assertFalse(ret, "IO didn't complete or failed on client")
        # self.is_io_running = False

        # # Start healing
        # ret = trigger_heal(self.mnode, self.volname)
        # self.assertTrue(ret, 'Heal is not started')
        # g.log.info('Healing is started')

        # # Monitor heal completion
        # ret = monitor_heal_completion(self.mnode, self.volname,
        #                               timeout_period=3600)
        # self.assertTrue(ret, 'Heal has not yet completed')

        # # Check if heal is completed
        # ret = is_heal_complete(self.mnode, self.volname)
        # self.assertTrue(ret, 'Heal is not complete')
        # g.log.info('Heal is completed successfully')

        # # Check for split-brain
        # ret = is_volume_in_split_brain(self.mnode, self.volname)
        # self.assertFalse(ret, 'Volume is in split-brain state')
        # g.log.info('Volume is not in split-brain state')
