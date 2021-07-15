"""
Copyright (C) 2016-2019  Red Hat, Inc. <http://www.redhat.com>

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
# TODO: nfs, cifs

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Test Script with Client Side Quorum with fixed should validate
        maximum number of bricks to accept

        * set cluster quorum to fixed
        * set cluster.quorum-count to higher number which is greater than
          number of replicas in a sub-voulme
        * Above step should fail
        """
        # set cluster.quorum-type to fixed
        options = {"cluster.quorum-type": "fixed"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])
        # get the subvolumes
        subvols_list = redant.get_subvols(self.vol_name, self.server_list[0])
        redant.logger.info(f"Number of subvolumes in volume {self.vol_name}"
                           f" is {len(subvols_list)}")

        # get the number of bricks in replica set
        num_bricks_in_subvol = len(subvols_list[0])
        redant.logger.info("Number of bricks in each replica "
                           f"set: {num_bricks_in_subvol}")

        # set cluster.quorum-count to higher value than the number
        # of bricks in replica set
        start_range = num_bricks_in_subvol + 1
        end_range = num_bricks_in_subvol + 30
        for i in range(start_range, end_range):
            options = {"cluster.quorum-count": f"{i}"}
            ret = redant.set_volume_options(self.vol_name, options,
                                            self.server_list[0],
                                            excep=False)
            if ret['msg']['opRet'] != '-1':
                raise Exception(f"Unexpected: Able to set {options} "
                                f"for volume {self.vol_name}, quorum-count"
                                " should not be greater than number of"
                                " bricks in replica set")
