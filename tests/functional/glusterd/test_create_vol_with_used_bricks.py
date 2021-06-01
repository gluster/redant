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
    Create volume using bricks of deleted volume
"""
from tests.nd_parent_test import NdParentTest

# nonDisruptive;dist-rep


class TestCase(NdParentTest):

    def run_test(self, redant):
        '''
        -> Create distributed-replica Volume
        -> Add 6 bricks to the volume
        -> Mount the volume
        -> Perform some I/O's on mount point
        -> unmount the volume
        -> Stop and delete the volume
        -> Create another volume using bricks of deleted volume
        -> Start the volume
        -> Execute IO command
        -> Mount the volume
        '''

        self.volume_type1 = 'dist-rep'
        self.volume_name1 = "test_create_vol_with_fresh_bricks"
        conf_dict = self.vol_type_inf[self.conv_dict[self.volume_type1]]
        redant.setup_volume(self.volume_name1, self.server_list[0],
                            conf_dict, self.server_list,
                            self.brick_roots, True)
        mul_factor = 6
        _, br_cmd = redant.form_brick_cmd(self.server_list,
                                          self.brick_roots,
                                          self.volume_name1,
                                          mul_factor, True)
        redant.add_brick(self.volume_name1,
                         br_cmd[1:], self.server_list[0],
                         True, replica_count=3)

        mountpoint = f"/mnt/{self.volume_name1}"
        redant.execute_abstract_op_node(f"mkdir -p {mountpoint}",
                                        self.client_list[0])
        redant.volume_mount(self.server_list[1], self.volume_name1,
                            mountpoint, self.client_list[0])
        # Run IOs
        redant.logger.info("Starting IO on all mounts...")
        self.all_mounts_procs = []
        self.mounts = (redant.es.
                       get_mnt_pts_dict_in_list(self.volume_name1))
        counter = 1

        for mount in self.mounts:
            redant.logger.info(f"Starting IO on {mount['client']}:"
                               f"{mount['mountpath']}")
            proc = redant.create_deep_dirs_with_files(mount['mountpath'],
                                                      counter, 2, 3, 4, 10,
                                                      mount['client'])
            self.all_mounts_procs.append(proc)
            counter = counter + 10

        # Validate IO
        if not redant.validate_io_procs(self.all_mounts_procs, self.mounts):
            raise Exception("IO failed on some of the clients")

        # Unmount the volume
        redant.volume_unmount(self.volume_name1,
                              mountpoint,
                              self.client_list[0])
        # get the list of all bricks
        bricks_list = redant.get_all_bricks(self.volume_name1,
                                            self.server_list[0])
        # Stop the volume
        redant.volume_stop(self.volume_name1, self.server_list[0])

        # Delete the volume
        redant.volume_delete(self.volume_name1, self.server_list[0])

        self.volname = "test_create_vol_used_bricks"

        brick_cmd = " ".join(bricks_list[0:6])

        cmd = (f"gluster volume create {self.volname}"
               f" replica 3 {brick_cmd} --mode=script")

        ret = redant.execute_abstract_op_node(cmd,
                                              self.server_list[0],
                                              False)
        if ret['error_code'] == 0:
            raise Exception("Volume creation should fail with"
                            " used bricks.")
        redant.logger.info("Volume creation failed as expected")

        # Checking failed message of volume creation
        err = ret['error_msg']
        msg = ' '.join(['volume create: test_create_vol_used_bricks: failed:',
                        bricks_list[0].split(':')[1],
                        'is already part of a volume'])
        if msg not in err:
            raise Exception("Incorrect error message for volume creation "
                            "with used bricks")
        redant.logger.info("Correct error message "
                           "for volume creation")
