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

# disruptive;rep,dist-rep
# TODO: nfs

from tests.d_parent_test import DParentTest


class TestClientSideQuorumTests(DParentTest):

    def run_test(self, redant):
        """
        * check the default value of cluster.quorum-type
        * try to set any junk value to cluster.quorum-type
          other than {none,auto,fixed}
        * check the default value of cluster.quorum-count
        * set cluster.quorum-type to fixed and cluster.quorum-count to 1
        * start I/O from the mount point
        * kill 2 of the brick process from the each replica set.
        * set cluster.quorum-type to auto

        """
        # check the default value of cluster.quorum-type
        option = "cluster.quorum-type"
        ret = redant.get_volume_options(self.vol_name, option,
                                        self.server_list[0])
        if ret['cluster.quorum-type'] != "auto":
            raise Exception(f"Default value for {option} is not auto"
                            f" for volume {self.vol_name}")

        # set the junk value to cluster.quorum-type
        junk_values = ["123", "abcd", "fixxed", "Aauto"]
        for each_junk_value in junk_values:
            options = {"cluster.quorum-type": each_junk_value}
            ret = redant.set_volume_options(self.vol_name, options,
                                            self.server_list[0], excep=False)
            if ret['msg']['opRet'] == '0':
                raise Exception(f"Able to set junk value {options} for "
                                f"volume {self.vol_name}")

        # check the default value of cluster.quorum-count
        option = "cluster.quorum-count"
        ret = redant.get_volume_options(self.vol_name, option,
                                        self.server_list[0])
        if ret['cluster.quorum-count'].split(" ")[0] != "(null)":
            raise Exception(f"Default value for {option} is not (null)"
                            f" for volume {self.vol_name}")

        # set cluster.quorum-type to fixed and cluster.quorum-count to 1
        options = {"cluster.quorum-type": "fixed",
                   "cluster.quorum-count": "1"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0],
                                  multi_option=True)

        # create files
        redant.logger.info("Starting IO on all mounts...")
        cmd = (f"python3 /tmp/file_dir_ops.py create_files "
               f"-f 10 --base-file-name file {self.mountpoint}")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # get the subvolumes
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        num_subvols = len(subvols)

        # bring bricks offline( 2 bricks ) for all the subvolumes
        for i in range(0, num_subvols):
            subvol_brick_list = subvols[i]
            bricks_to_bring_offline = subvol_brick_list[0:2]
            if not redant.bring_bricks_offline(self.vol_name,
                                               bricks_to_bring_offline):
                raise Exception("Failed to bring down the bricks. Please "
                                "check the log file for more details.")

        # create files
        redant.logger.info("Starting IO on all mounts...")
        cmd = (f"python3 /tmp/file_dir_ops.py create_files "
               f"-f 10 --base-file-name second_file {self.mountpoint}")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # set cluster.quorum-type to auto
        options = {"cluster.quorum-type": "auto"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # create files
        all_mounts_procs = []
        redant.logger.info("Starting IO on all mounts...")
        cmd = (f"mkdir {self.mountpoint}/newdir && touch {self.mountpoint}/"
               "newdir/myfile{1..3}.txt")
        proc = redant.execute_command_async(cmd, self.client_list[0])
        all_mounts_procs.append(proc)

        # Validate IO
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        ret, _ = redant.is_io_procs_fail_with_error(all_mounts_procs,
                                                    self.mounts)
        if not ret:
            raise Exception("Unexpected error and IO successful"
                            " on not connected transport endpoint")
