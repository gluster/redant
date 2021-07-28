"""
Copyright (C) 2021 Red Hat, Inc. <http://www.redhat.com>

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
    Test Cases in this module related to Glusterd volume status while
    IOs in progress
"""
# disruptive;rep,dist-rep

import traceback
import random
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):

        try:
            ret = self.redant.wait_for_io_to_complete(self.all_mounts_procs,
                                                      self.mounts)
            if not ret:
                raise Exception("IO failed to complete")
            self.redant.profile_stop(self.vol_name,
                                     random.choice(self.server_list))

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Create and start the volume
        """
        conf_hash = self.vol_type_inf[self.volume_type]
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots, force=True)

    def run_test(self, redant):
        '''
        Create replica volume then mount the volume, once
        volume mounted successfully on client, start running IOs on
        mount point then run the "gluster volume <volname> profile info"
        command on all clusters randomly.
        Then check that IOs completed successfully or not on mount point.
        Check that files in mount point listing properly or not.
        check the release directory value should be less or equals '4'
        '''

        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        status_on = "on"
        validate_profiles = ('cluster.eager-lock',
                             'diagnostics.count-fop-hits',
                             'diagnostics.latency-measurement')

        redant.profile_start(self.vol_name,
                             random.choice(self.server_list))

        for validate_profile in validate_profiles:
            out = redant.get_volume_options(self.vol_name,
                                            validate_profile,
                                            random.choice(self.server_list))
            if out is None:
                raise Exception("Failed to get volume option"
                                f" {validate_profile}")
        # Mounting a volume
        self.mountpoint = f"/mnt/{self.vol_name}"
        for client in self.client_list:
            redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                            client)
            redant.volume_mount(self.server_list[0],
                                self.vol_name,
                                self.mountpoint, client)

        # run IOs
        self.counter = 1
        for mount_obj in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      self.counter,
                                                      2, 15, 5, 25,
                                                      mount_obj['client'])
            self.all_mounts_procs.append(proc)
            self.counter = self.counter + 10

        # this command should not get hang while io is in progress
        for _ in range(20):
            ret = redant.profile_info(self.vol_name,
                                      random.choice(self.server_list))
            if ret is None:
                raise Exception("Failed to get the profile info")

        # Validate IO
        ret = self.redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO validation failed")

        # List all files and dirs created
        if not (redant.
                list_all_files_and_dirs_mounts(self.mounts)):
            raise Exception("Failed to list files and dirs")

        cmd = (f"gluster v profile {self.vol_name} info | grep OPENDIR"
               " | awk '{print$8}'")
        ret = redant.execute_abstract_op_node(cmd,
                                              random.choice(self.server_list))
        out = ret['msg']
        if out is None:
            raise Exception(f"Failed to get volume {self.vol_name}"
                            " profile info")

        for value in out:
            if value.rstrip("\n") > '4':
                raise Exception("Failed to validate profile"
                                f" info on volume {self.vol_name}")
