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
    Tetstcase involves killing brick in cyclic order and
    listing the directories after healing from mount point
"""
# disruptive;rep,dist-rep
# TODO: nfs

import time
import traceback
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        try:
            ret = self.redant.wait_for_io_to_complete(self.list_of_procs,
                                                      self.mnt_list)
            if not ret:
                raise Exception("IO failed on some of the clients")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """""
        Description:-
        - I/O on the mounts
        - kill brick in cyclic order
        - list the files after healing
        """""

        # IO on the mount point
        # Each client will write 2 files each of 1 MB and keep
        # modifying the same file
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.list_of_procs = []
        for mount_obj in self.mnt_list:
            redant.logger.info(f"Starting IO on {mount_obj['client']}:"
                               f"{mount_obj['mountpath']}")
            bs_fil = f"test_brick_down_from_client_{mount_obj['client']}.txt"
            proc = redant.create_files(num_files=2,
                                       fix_fil_size="1M",
                                       path=mount_obj['mountpath'],
                                       node=mount_obj['client'],
                                       base_file_name=bs_fil)
            self.list_of_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(self.list_of_procs, self.mnt_list)
        if not ret:
            raise Exception("IO validation failed")

        # Killing bricks in cyclic order
        bricks_list = redant.get_all_bricks(self.vol_name, self.server_list[0])

        if bricks_list is None:
            raise Exception("Failed to get the bricks list")

        # Total number of cyclic brick-down cycles to be executed
        number_of_cycles = 0
        while number_of_cycles < 3:
            number_of_cycles += 1
            for brick in bricks_list:
                # Bring brick offline
                redant.bring_bricks_offline(self.vol_name, [brick])

                if not redant.are_bricks_offline(self.vol_name,
                                                 brick,
                                                 self.server_list[0]):
                    raise Exception(f"Brick {brick} is not offline")

                # Introducing 30 second sleep when brick is down
                time.sleep(30)

                # Bring brick online
                redant.bring_bricks_online(self.vol_name, self.server_list,
                                           [brick])

                # Check if bricks are online
                if not redant.are_bricks_online(self.vol_name, [brick],
                                                self.server_list[0]):
                    raise Exception(f"Brick {brick} is not online.")

                # Check daemons
                if not (redant.
                        are_all_self_heal_daemons_online(self.vol_name,
                                                         self.server_list[0])):
                    raise Exception("Some of the self-heal Daemons"
                                    " are offline")

        # Checking volume status
        if not (redant.
                log_volume_info_and_status(self.server_list[0],
                                           self.vol_name)):
            raise Exception("Logging volume info and status failed on "
                            f"volume {self.vol_name}")

        # Monitoring heals on the volume
        if not (redant.
                monitor_heal_completion(self.server_list[0],
                                        self.vol_name)):
            raise Exception("Self heal didn't complete even after waiting "
                            "for 20 minutes.")

        # List all files and dirs created
        ret = redant.list_all_files_and_dirs_mounts(self.mnt_list)
        if not ret:
            raise Exception("Failed to list all files and dirs")
