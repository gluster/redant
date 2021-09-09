"""
 Copyright (C) 2020 Red Hat, Inc. <http://www.redhat.com>

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
    The testcase covers negative lookup of a directory in distributed-
    replicated and distributed-dispersed volumes
"""

# nonDisruptive;dist-disp,dist-rep,dist-arb
from random import choice
from tests.nd_parent_test import NdParentTest


class TestNoFreshLookUpBrickDown(NdParentTest):

    def _do_lookup(self, dirname):
        """
        Performes a look up on the directory.
        """
        ret = self.redant.path_exists(self.client_list[0], dirname)
        if not ret:
            raise Exception(f"Directory {dirname} doesn't exists ")

    def _match_occurences(self, first_count, search_pattern, filename):
        """
        Validating the count of the search pattern before and after
        lookup.
        """
        ret = self.redant.occurences_of_pattern_in_file(self.client_list[0],
                                                        search_pattern,
                                                        filename)
        if ret != first_count:
            raise Exception("Failed: The lookups logged for the directory "
                            "are more than expected")

    def run_test(self, redant):
        """
        Steps:
        1. Mount the volume on one client.
        2. Create a directory
        3. Validate the number of lookups for the directory creation from the
           log file.
        4. Perform a new lookup of the directory
        5. No new lookups should have happened on the directory, validate from
           the log file.
        6. Bring down one subvol of the volume and repeat step 4, 5
        7. Bring down one brick from the online bricks and repeat step 4, 5
        8. Start the volume with force and wait for all process to be online.
        """
        # Set client log level to DEBUG
        options = {'diagnostics.client-log-level': 'DEBUG'}
        self.redant.set_volume_options(self.vol_name, options,
                                       self.server_list[0])

        # Distinct log file for the validation of this test
        filename = f"/var/log/glusterfs/mnt-{self.vol_name}.log"

        # Creating a dir on the mount point.
        redant.create_dir(self.mountpoint, "dir1", self.client_list[0])

        search_pattern = "/dir1: Calling fresh lookup"

        # Check log file for the pattern in the log file
        first_cnt = redant.occurences_of_pattern_in_file(self.client_list[0],
                                                         search_pattern,
                                                         filename)
        if first_cnt <= 0:
            raise Exception("Unable to find pattern in the given file")

        # Perform a lookup of the directory dir1
        dirname = f"{self.mountpoint}/dir1"
        self._do_lookup(dirname)

        # Recheck for the number of lookups from the log file
        self._match_occurences(first_cnt, search_pattern, filename)

        # Bring down one subvol of the volume
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get the subvols")

        brick_list = choice(subvols)
        ret = redant.bring_bricks_offline(self.vol_name, brick_list)
        if not ret:
            raise Exception("Unable to bring the given bricks offline")

        # Do a lookup on the mountpoint for the directory dir1
        self._do_lookup(dirname)

        # Re-check the number of occurences of lookup
        self._match_occurences(first_cnt, search_pattern, filename)

        # From the online bricks, bring down one brick
        online_bricks = redant.get_online_bricks_list(self.vol_name,
                                                      self.server_list[0])
        if not online_bricks:
            raise Exception("Unable to fetch online bricks")

        offline_brick = choice(online_bricks)
        ret = redant.bring_bricks_offline(self.vol_name, offline_brick)
        if not ret:
            raise Exception(f"Unable to bring the brick {offline_brick} "
                            "offline")

        # Do a lookup on the mounpoint and check for new lookups from the log
        self._do_lookup(dirname)
        self._match_occurences(first_cnt, search_pattern, filename)

        # Start volume with force
        redant.volume_start(self.vol_name, self.server_list[0], force=True)

        # Wait for all the processess to be online.
        if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.server_list[0], self.server_list)):
            raise Exception("Few volume processess are offline for the "
                            f"volume: {self.vol_name}")
