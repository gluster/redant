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
    TC to check heal process on EC volume when brick is brought
    down in a cyclic fashion
"""

# disruptive;disp,dist-disp
# TODO: NFS
from datetime import datetime, timedelta
from time import sleep
import traceback
from tests.d_parent_test import DParentTest


class TestIOsOnECVolume(DParentTest):

    def terminate(self):
        """
        Wait for IO to complete if the TC fails midway
        """
        try:
            if self.is_io_running:
                if not (self.redant.wait_for_io_to_complete(
                        self.all_mounts_procs, self.mnt_list)):
                    raise Exception("Failed to wait for IO to complete")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _bring_bricks_online_and_monitor_heal(self, bricks):
        """Bring the bricks online and monitor heal until completion"""
        self.redant.volume_start(self.vol_name, self.server_list[0],
                                 force=True)
        if not self.redant.monitor_heal_completion(self.server_list[0],
                                                   self.vol_name,
                                                   bricks=bricks):
            raise Exception("Heal is not yet completed")

    def run_test(self, redant):
        """
        Steps:
        - Create, start and mount an EC volume in two clients
        - Create multiple files and directories including all file types on one
          directory from client 1
        - Take arequal check sum of above data
        - Create another folder and pump different fops from client 2
        - Fail and bring up redundant bricks in a cyclic fashion in all of the
          subvols maintaining a minimum delay between each operation
        - In every cycle create new dir when brick is down and wait for heal
        - Validate heal info on volume when brick down erroring out instantly
        - Validate arequal on brining the brick offline
        """
        self.is_io_running = False
        # Check for 2 clients in the cluster
        redant.check_hardware_requirements(clients=self.client_list,
                                           clients_count=2)

        # Create a directory structure on mount from client 1
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        cmd = ("python3 /usr/share/redant/script/file_dir_ops.py"
               " create_deep_dirs_with_files --dir-depth 3"
               " --max-num-of-dirs 5 --fixed-file-size 10k "
               f"--num-of-files 9 {self.mounts[0]['mountpath']}")
        redant.execute_abstract_op_node(cmd, self.mounts[0]['client'])

        dir_name = 'user1'
        for i in range(5):
            sfile = f"{self.mountpoint}/{dir_name}/testfile{i}.txt"
            link_file = f"{self.mountpoint}/{dir_name}/testfile{i}_sl.txt"
            ret = redant.create_link_file(self.mounts[0]['client'], sfile,
                                          link_file, soft=True)
            if not ret:
                raise Exception("Failed to create soft link")

        for i in range(5, 9):
            sfile = f"{self.mountpoint}/{dir_name}/testfile{i}.txt"
            link_file = f"{self.mountpoint}/{dir_name}/testfile{i}_hl.txt"
            ret = redant.create_link_file(self.mounts[0]['client'], sfile,
                                          link_file)
            if not ret:
                raise Exception("Failed to create soft link")

        # Take note of arequal checksum
        exp_arequal = redant.collect_mounts_arequal(self.mounts[0], dir_name)

        # Get all the subvols in the volume
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception('Not able to get subvols of the volume')

        # Create a dir, pump IO in that dir, offline b1, wait for IO and
        # online b1, wait for heal of b1, bring b2 offline...
        m_point, m_client = (self.mounts[1]['mountpath'],
                             self.mounts[1]['client'])
        cur_off_bricks = ''
        self.all_mounts_procs = []
        self.mnt_list = []
        for count, off_brick in enumerate(zip(*subvols),
                                          start=1):

            # Bring offline bricks online by force starting volume
            if cur_off_bricks:
                self._bring_bricks_online_and_monitor_heal(cur_off_bricks)

            # Create a dir for running IO
            redant.create_dir(m_point, f'dir{count}', m_client)

            # Start IO in the newly created directory
            cmd = (f"python3 /usr/share/redant/script/fd_writes.py -n 10"
                   f" -t 480 -d 5 -c 16 --dir {m_point}/dir{count}")
            proc = redant.execute_command_async(cmd, m_client)
            self.all_mounts_procs.append(proc)
            self.is_io_running = True
            self.mnt_list.append(self.mounts[1])

            # Wait IO to partially fill the dir
            sleep(10)

            # Bring a single brick offline from all of subvols
            ret = redant.bring_bricks_offline(self.vol_name, list(off_brick))
            if not ret:
                raise Exception(f"Not able to bring {off_brick} offline")

            # Validate heal info errors out, on brining bricks offline in < 5s
            start_time = datetime.now().replace(microsecond=0)
            ret = redant.get_heal_info(self.server_list[0], self.vol_name)
            end_time = datetime.now().replace(microsecond=0)
            if not ret:
                raise Exception('Not able to query heal info status '
                                'of volume when a brick is offline')
            if end_time - start_time >= timedelta(seconds=5):
                raise Exception('Query of heal info of volume when a brick is'
                                ' offline is taking more than 5 seconds')

            # Wait for some more IO to fill dir
            sleep(10)

            # Validate arequal on initial static dir
            act_arequal = redant.collect_mounts_arequal(self.mounts[0],
                                                        dir_name)
            if exp_arequal != act_arequal:
                raise Exception('Mismatch of arequal checksum before and'
                                ' after killing a brick')

            cur_off_bricks = off_brick

        # Take note of ctime on mount
        ret = redant.execute_abstract_op_node('date +%s', m_client)
        prev_ctime = float(ret['msg'][0].strip())

        self._bring_bricks_online_and_monitor_heal(cur_off_bricks)

        # Validate IO was happening during brick operations
        # and compare ctime of recent file to current epoch time
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mnt_list)
        if not ret:
            raise Exception('Not able to validate completion of IO on mounts')
        self.is_io_running = False

        cmd = (f"find {m_point} -printf '%C@\n'"" -type f | sort -r | "
               "head -n 1")
        ret = redant.execute_abstract_op_node(cmd, m_client)
        curr_ctime = float(ret['msg'][0].strip())
        if curr_ctime <= prev_ctime:
            raise Exception('Not able to validate IO was happening '
                            'during brick operations')
