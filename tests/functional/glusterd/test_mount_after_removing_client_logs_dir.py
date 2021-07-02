"""
 Copyright (C) 2019-2020  Red Hat, Inc. <http://www.redhat.com>

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License along`
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

 Description:
    A testcase to remove /var/log/glusterfs/ on client, mounting a volume
    and createing a file and a dir on it.
"""

import traceback
from tests.d_parent_test import DParentTest

# disruptive;dist,dist-rep,rep,disp,dist-disp


class TestCase(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = self.vol_type_inf[self.volume_type]
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)

    def terminate(self):

        # Resetting the /var/log/glusterfs on client
        # and archiving the present one.
        try:
            cmd = ('for file in `ls /var/log/glusterfs/`; do '
                   'mv /var/log/glusterfs/$file'
                   ' /var/log/glusterfs/`date +%s`-$file; done')
            self.redant.execute_abstract_op_node(cmd, self.client_list[0])

            cmd = ('mv /root/glusterfs/* /var/log/glusterfs/;'
                   'rm -rf /root/glusterfs')
            self.redant.execute_abstract_op_node(cmd, self.client_list[0])

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test Case:
        1. Create all types of volumes.
        2. Start all volumes.
        3. Delete /var/log/glusterfs folder on the client.
        4. Mount all the volumes one by one.
        5. Run IO on all the mount points.
        6. Check if logs are generated in /var/log/glusterfs/.
        """

        # Removing dir /var/log/glusterfs on client.
        cmd = 'mv /var/log/glusterfs /root/'
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Mounting the volume.
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                             self.client_list[0])
        redant.volume_mount(self.server_list[0], self.vol_name,
                            self.mountpoint, self.client_list[0])

        # Running IO on the mount point.
        # Creating a dir on the mount point.
        redant.create_dir(self.mountpoint, "dir2", self.client_list[0])

        # Creating a file on the mount point.
        cmd = f"touch  {self.mountpoint}/file"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Checking if logs are regenerated or not.
        ret = redant.get_dir_contents('/var/log/glusterfs/',
                                      self.client_list[0])
        if ret is None:
            raise Exception("Log files were not regenerated")

        # Moving the logs back in place, and archiving the old ones
        cmd = ('for file in `ls /var/log/glusterfs/`; do '
               'mv /var/log/glusterfs/$file'
               ' /var/log/glusterfs/`date +%s`-$file; done')
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        cmd = ('mv /root/glusterfs/* /var/log/glusterfs/;'
               'rm -rf /root/glusterfs')
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Merged TC test_mount_remove_client_logs_dir_remount
        # 1. Delete /var/log/glusterfs folder on client.
        # 4. Run IO on all the mount points.
        # 5. Unmount and remount all volumes.
        # 6. Check if logs are regenerated or not.

        # Removing dir /var/log/glusterfs on client.
        cmd = 'mv /var/log/glusterfs /root/'
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Running IO on the mount point.
        # Creating a dir on the mount point.
        redant.create_dir(self.mountpoint, "dir", self.client_list[0])

        # Creating a file on the mount point.
        cmd = f"touch  {self.mountpoint}/file1"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Unmounting and remounting volume.
        redant.volume_unmount(self.vol_name, self.mountpoint,
                              self.client_list[0])

        redant.volume_mount(self.server_list[0], self.vol_name,
                            self.mountpoint, self.client_list[0])

        # Checking if logs are regenerated or not.
        ret = redant.get_dir_contents('/var/log/glusterfs/',
                                      self.client_list[0])
        if ret is None:
            raise Exception("Log files were not regenerated")
