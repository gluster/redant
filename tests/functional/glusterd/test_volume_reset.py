"""
 Copyright (C) 2017-2018  Red Hat, Inc. <http://www.redhat.com>

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
    Test volume reset validations
"""

# disruptive;dist,rep,disp,dist-rep,disp,dist-disp
from tests.nd_parent_test import NdParentTest


class GlusterdVolumeReset(NdParentTest):

    def run_test(self, redant):
        """
        -> Create volume
        -> Enable BitD, Scrub and Uss on volume
        -> Verify  the BitD, Scrub and Uss  daemons are running on every node
        -> Reset the volume
        -> Verify the Daemons (BitD, Scrub & Uss ) are running or not
        -> Eanble Uss on same volume
        -> Reset the volume with force
        -> Verify all the daemons(BitD, Scrub & Uss) are running or not
        """

        # enable bitrot and scrub on volume
        redant.enable_bitrot(self.vol_name, self.server_list[0])

        # enable uss on volume
        redant.enable_uss(self.vol_name, self.server_list[0])

        # Checks bitd, snapd, scrub daemons running or not
        node_list = []
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if brick_list is None:
            raise Exception("Failed to get brick list")

        for brick in brick_list:
            node, _ = brick.split(':')
            node_list.append(node)

        for node in node_list:
            if not redant.is_bitd_running(self.vol_name, node):
                raise Exception(f"Bitrot Daemon is not running on {node}")
            if not redant.is_scrub_process_running(self.vol_name, node):
                raise Exception(f"Scrub Daemon is not running on {node}")
            if not redant.is_snapd_running(self.vol_name, node):
                raise Exception(f"Snap Daemon is not running on {node}")

        # command for volume reset
        redant.volume_reset(self.vol_name, self.server_list[0])

        # After volume reset snap daemon will not be running,
        # bitd and scrub daemons will be in running state.
        for node in node_list:
            if not redant.is_bitd_running(self.vol_name, node):
                raise Exception(f"Bitrot Daemon is not running on {node}")
            if not redant.is_scrub_process_running(self.vol_name, node):
                raise Exception(f"Scrub Daemon is not running on {node}")
            if redant.is_snapd_running(self.vol_name, node):
                raise Exception(f"Snap Daemon is still running on {node}")

        # enable uss on volume
        redant.enable_uss(self.vol_name, self.server_list[0])

        # command for volume reset with force
        redant.volume_reset(self.vol_name, self.server_list[0], True)

        # After volume reset bitd, snapd, scrub daemons will not be running,
        # all three daemons will get die
        for node in node_list:
            if redant.is_bitd_running(self.vol_name, node):
                raise Exception(f"Bitrot Daemon is still running on {node}")
            if redant.is_scrub_process_running(self.vol_name, node):
                raise Exception(f"Scrub Daemon is still running on {node}")
            if redant.is_snapd_running(self.vol_name, node):
                raise Exception(f"Snap Daemon is still running on {node}")
