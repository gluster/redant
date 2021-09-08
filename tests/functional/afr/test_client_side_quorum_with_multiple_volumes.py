"""
 Copyright (C) 2016-2020  Red Hat, Inc. <http://www.redhat.com>

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
    Test Cases in this module tests the client side quorum.
"""

# disruptive;dist-rep
from tests.d_parent_test import DParentTest


class TestClientSideQuorumTestsMultipleVols(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        # Create and start multiple volumes
        self.mounts_list = []
        self.mount_points_and_volnames = {}
        for i in range(1, 5):
            conf_hash = self.vol_type_inf['dist-rep'].copy()
            if i < 3:
                conf_hash['dist_count'] = 2
            vol_name = f"testvol-{self.volume_type}-{i}"
            self.redant.setup_volume(vol_name, self.server_list[0],
                                     conf_hash, self.server_list,
                                     self.brick_roots, force=True)
            mountpoint = (f"/mnt/{vol_name}")
            self.redant.execute_abstract_op_node(f"mkdir -p {mountpoint}",
                                                 self.client_list[0])
            self.redant.volume_mount(self.server_list[0],
                                     vol_name,
                                     mountpoint, self.client_list[0])
            self.mounts_list.append(mountpoint)
            self.mount_points_and_volnames[vol_name] = mountpoint

        conf_hash = self.vol_type_inf['dist'].copy()
        vol_name = f"testvol-{self.volume_type}-5"
        self.redant.setup_volume(vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots, force=True)
        mountpoint = (f"/mnt/{vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p {mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0],
                                 vol_name,
                                 mountpoint, self.client_list[0])
        self.mounts_list.append(mountpoint)
        self.mount_points_and_volnames[vol_name] = mountpoint

    def run_test(self, redant):
        """
        - create four volume as below
            vol1->2x2
            vol2->2x2
            vol3->2x3
            vol4->2x3
            vol5->a pure distribute volume
        - do IO to all vols
        - set client side quorum to auto for vol1 and vol3
        - get the client side quorum value for all vols and check for result
        - bring down b0 on vol1 and b0 and b1 on vol3
        - try to create files on all vols and check for result
        """
        # Creating files for all volumes
        for mount_point in self.mounts_list:
            self.all_mounts_procs = []
            command = (f"python3 /usr/share/redant/script/file_dir_ops.py "
                       "create_files -f 50 --fixed-file-size 1k"
                       f" {mount_point}")
            proc = redant.execute_command_async(command, self.client_list[0])
            self.all_mounts_procs.append(proc)

            # Validate IO
            mounts = {
                "client": self.client_list[0],
                "mountpath": mount_point
            }
            if not redant.validate_io_procs(self.all_mounts_procs, mounts):
                raise Exception("IO failed on some of the clients")

        volumes_to_change_options = ['1', '3']
        # set cluster.quorum-type to auto
        for vol_number in volumes_to_change_options:
            vol_name = f"testvol-dist-rep-{vol_number}"
            options = {"cluster.quorum-type": "auto"}
            redant.set_volume_options(vol_name, options, self.server_list[0])

        # check if options are set correctly
        volume_list = redant.get_volume_list(self.server_list[0])
        if len(volume_list) == 0:
            raise Exception("Failed to get the volume list")
        for volume in volume_list:
            option = 'cluster.quorum-type'
            ret = redant.get_volume_options(volume, option,
                                            self.server_list[0])
            if (volume == 'testvol-dist-rep-1'
               or volume == 'testvol-dist-rep-3'):
                if ret['cluster.quorum-type'] != 'auto':
                    raise Exception("Option cluster.quorum-type is not AUTO"
                                    f" for {volume}")

        # Get first brick server and brick path
        # and get first file from filelist then delete it from volume
        vols_file_list = {}
        for volume in volume_list:
            brick_list = redant.get_all_bricks(volume, self.server_list[0])
            if not brick_list:
                raise Exception("Failed to get the brick list")
            brick_server, brick_path = brick_list[0].split(':')
            ret = redant.execute_abstract_op_node(f"ls {brick_path}",
                                                  brick_server)
            files = " ".join(ret['msg'])
            file_from_vol = files.splitlines()[0]
            redant.execute_abstract_op_node(f"rm -rf {brick_path}/"
                                            f"{file_from_vol}", brick_server)
            vols_file_list[volume] = file_from_vol

        # bring brick offline of 'testvol-dist-rep-1' and 'testvol-dist-rep-3'
        for volname in ('testvol-dist-rep-1', 'testvol-dist-rep-3'):
            brick_list = redant.get_all_bricks(volname, self.server_list[0])
            if not brick_list:
                raise Exception("Failed to get the brick list")
            bricks_to_bring_offline = brick_list[0:2]
            redant.bring_bricks_offline(volname, bricks_to_bring_offline)

            if not redant.are_bricks_offline(volname, bricks_to_bring_offline,
                                             self.server_list[0]):
                raise Exception(f"Bricks {bricks_to_bring_offline} are not"
                                " offline")

        # merge two dicts (volname: file_to_delete) and (volname: mountpoint)
        temp_dict = [vols_file_list, self.mount_points_and_volnames]
        file_to_delete_to_mountpoint_dict = {}
        for k in vols_file_list:
            file_to_delete_to_mountpoint_dict[k] = (
                tuple(file_to_delete_to_mountpoint_dict[k]
                      for file_to_delete_to_mountpoint_dict in
                      temp_dict))

        # create files on all volumes and check for result
        for volname, file_and_mountpoint in (
                file_to_delete_to_mountpoint_dict.items()):
            filename, mountpoint = file_and_mountpoint
            mounts = {
                "client": self.client_list[0],
                "mountpath": mountpoint
            }
            # check for ROFS error for testvol-dist-rep-1 and
            # testvol-dist-rep-3
            if (volname == 'testvol-dist-rep-1'
               or volname == 'testvol-dist-rep-3'):
                # create new file taken from vols_file_list
                all_mounts_procs = []
                cmd = f"touch {mountpoint}/{filename}"
                proc = redant.execute_command_async(cmd, self.client_list[0])
                all_mounts_procs.append(proc)

                # Validate IO
                ret, _ = redant.is_io_procs_fail_with_error(all_mounts_procs,
                                                            mounts)
                if not ret:
                    raise Exception("Unexpected error and IO successful"
                                    " on read-only filesystem")

            # check for no errors for all the rest volumes
            else:
                # create new file taken from vols_file_list
                all_mounts_procs = []
                cmd = f"touch {mountpoint}/{filename}"
                proc = redant.execute_command_async(cmd, self.client_list[0])
                all_mounts_procs.append(proc)

                # Validate IO
                if not redant.validate_io_procs(all_mounts_procs,
                                                mounts):
                    raise Exception("IO failed on some of the clients")
