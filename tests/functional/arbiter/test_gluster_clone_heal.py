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
    TC to check heal when gluster compiled on client
"""

# disruptive;arb,dist-arb,rep,dist-rep
import traceback
from tests.d_parent_test import DParentTest


class TestGlusterCloneHeal(DParentTest):

    def terminate(self):
        """
        Wait for IO to complete, if TC fails in between
        """
        try:
            if not self.io_validation_complete:
                if not self.redant.wait_for_io_to_complete(self.proc_list,
                                                           self.mount):
                    raise Exception("Failed to wait for IO to complete")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test gluster compilation on mount point(Heal command)
        - Creating directory test_compilation
        - Compile gluster on mountpoint
        - Select bricks to bring offline
        - Bring brick offline
        - Validate IO
        - Bring bricks online
        - Wait for volume processes to be online
        - Verify volume's all process are online
        - Monitor heal completion
        - Check for split-brain
        - Get arequal after getting bricks online
        - Compile gluster on mountpoint again
        - Repeat the above steps
        """
        # Creating directory test_compilation
        redant.create_dir(self.mountpoint, "test_compilation",
                          self.client_list[0])

        # Perform compilation check two times
        self.proc_list = []
        self.io_validation_complete = False
        self.mount = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }

        # Compile gluster on mountpoint
        cmd = (f"cd {self.mountpoint}/test_compilation; rm -rf glusterfs; "
               "git clone git://github.com/gluster/glusterfs.git; "
               "cd glusterfs; ./autogen.sh; ./configure "
               "CFLAGS='-g3 -O0 -DDEBUG'; make; cd ../..;")
        proc = redant.execute_command_async(cmd, self.client_list[0])
        self.proc_list.append(proc)

        # Select bricks to bring offline
        offline_brick_list = (redant.select_volume_bricks_to_bring_offline(
                              self.vol_name, self.server_list[0]))

        # Killing one brick from the volume set
        if not redant.bring_bricks_offline(self.vol_name,
                                           offline_brick_list):
            raise Exception("Failed to bring bricks offline")

        # Validate if bricks are offline
        if not redant.are_bricks_offline(self.vol_name, offline_brick_list,
                                         self.server_list[0]):
            raise Exception(f"Bricks {offline_brick_list} are not offline")

        # Validate IO
        ret = self.redant.validate_io_procs(self.proc_list, self.mount)
        if not ret:
            raise Exception("IO validation failed")
        self.io_validation_complete = True

        # Bring bricks online
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          offline_brick_list):
            raise Exception("Failed to bring bricks online")

        # Wait for volume processes to be online
        if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.server_list[0], self.server_list)):
            raise Exception("Failed to wait for volume processes to "
                            "be online")

        # Verify volume's all process are online
        if not (redant.verify_all_process_of_volume_are_online(self.vol_name,
                self.server_list[0])):
            raise Exception("All process are not online")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal has not yet completed")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume is in split-brain state")

        # Get arequal after getting bricks online
        redant.collect_mounts_arequal(self.mount)
