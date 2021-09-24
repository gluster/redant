"""
 Copyright (C) 2017-2018 Red Hat, Inc. <http://www.redhat.com>

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
 Test - Distribution based on hash value

 Description:
    TC to test DHT of files and directories based on hash value
"""

# disruptive;rep,dist,dist-rep,disp,dist-disp
from common.ops.gluster_ops.constants import \
    (FILETYPE_DIRS, TEST_LAYOUT_IS_COMPLETE,
     TEST_FILE_EXISTS_ON_HASHED_BRICKS)
import traceback
from tests.d_parent_test import DParentTest


class TestDHTHashValue(DParentTest):

    def terminate(self):
        """
        Remove the temp folder
        """
        try:
            cmd = f"rm -rf {self.temp_folder}"
            for mount_obj in self.mounts:
                self.redant.execute_abstract_op_node(cmd, mount_obj['client'],
                                                     False)
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Steps:
        - Create and start a volume
        - Mount it on clients
        - Create a directory on client node, and create some files with
          data in it.
        - Copy the files to the mountpoint
        - Validate LAYOUT on the mountpoint
        - Check xattrs on mountpoint
        """
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.temp_folder = "/tmp/temp_folder_for_testing"

        for mount_obj in self.mounts:
            client_host = mount_obj['client']
            mountpoint = mount_obj['mountpath']

            # Create directory for initial data
            cmd = f"mkdir {self.temp_folder}"
            redant.execute_abstract_op_node(cmd, client_host)

            # Prepare a set of data
            files = []
            for i in range(100):
                text = "Lorem Ipsum dummy text"
                cmd = f"echo {text} > {self.temp_folder}/file_{i}.txt"
                redant.execute_abstract_op_node(cmd, client_host)
                files.append(f"file_{i}.txt")

            # Copy prepared data to mount point
            cmd = f'cp -vr {self.temp_folder}/* {mountpoint}'
            redant.execute_abstract_op_node(cmd, client_host)

            # Verify that hash layout values are set on each
            # bricks for the dir
            ret = (redant.validate_files_in_dir(client_host, mountpoint,
                   test_type=TEST_LAYOUT_IS_COMPLETE))
            if not ret:
                raise Exception("TEST_LAYOUT_IS_COMPLETE: FAILED")

            ret = (redant.validate_files_in_dir(client_host, mountpoint,
                   test_type=TEST_FILE_EXISTS_ON_HASHED_BRICKS,
                   file_type=FILETYPE_DIRS))
            if not ret:
                raise Exception("TEST_FILE_EXISTS_ON_HASHED_BRICKS: FAILED")

            # Verify "trusted.gfid" extended attribute of the
            # directory/file on all the bricks
            gfids = dict()
            brick_list = redant.get_all_bricks(self.vol_name,
                                               self.server_list[0])
            for brick_item in brick_list:
                brick_host, brick_dir = brick_item.split(':')

                for target_dest in files:
                    if not (redant.path_exists(brick_host,
                            f'{brick_dir}/{target_dest}')):
                        continue
                    ret = redant.get_fattr(f'{brick_dir}/{target_dest}',
                                           'trusted.gfid', brick_host)
                    attr_val = ret[1].split('=')[1]
                    gfids.setdefault(target_dest, []).append(attr_val[1:-1])

            # Check if trusted.gfid is same on all the bricks
            if not all([False if len(set(gfids[k])) > 1 else True
                        for k in gfids]):
                raise Exception("trusted.gfid should be same on all bricks")

            # Verify that mount point shows pathinfo xattr.
            redant.get_fattr(mountpoint, 'trusted.glusterfs.pathinfo',
                             client_host)

            # Mount point should not display xattr:
            # trusted.gfid and trusted.glusterfs.dht
            attributes = redant.get_fattr_list(mountpoint, client_host)

            if 'trusted.gfid' in attributes:
                raise Exception("Expected: Mount point shouldn't display "
                                "xattr: 'trusted.gfid'")

            if 'trusted.glusterfs.dht' in attributes:
                raise Exception("Expected: Mount point shouldn't display "
                                "xattr: 'trusted.glusterfs.dht'")
