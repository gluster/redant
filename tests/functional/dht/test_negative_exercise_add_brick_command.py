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

 Description:
    Negative test - Exercise Add-brick command
"""

# disruptive;rep,dist,dist-rep,disp,dist-disp
from tests.d_parent_test import DParentTest


class TestExerciseAddbrickCommand(DParentTest):

    def run_test(self, redant):
        """Test add-brick command without volume"""
        # Form bricks list for add-brick
        brick_cmd = redant.form_brick_cmd_to_add_brick(self.server_list[0],
                                                       self.vol_name,
                                                       self.server_list,
                                                       self.brick_roots)
        cmd = f"gluster volume add-brick {brick_cmd}"
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0], False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: Add-brick is successfull")

        # Case 2: test_add_duplicate_brick
        """
        Test add-bricks to the volume which are already part of the volume
        """
        # Get sub-vols for adding the same bricks to the volume
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        cmd = (f"gluster volume add-brick {self.vol_name} "
               f"{' '.join(subvols[0])}")
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0], False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: Add-brick is successfull")
        err_msg = ("Brick may be containing or be contained by an existing"
                   " brick")
        if err_msg not in ret['error_msg']:
            raise Exception("Unexpected: add-brick is successful without any"
                            " error")

        # Case 3: test_add_nested_brick
        """Test add nested bricks to the volume"""
        # Get sub-vols for forming a nested bricks list
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])[0]
        nested_bricks_list = [f"{x}/nested" for x in subvols]
        cmd = (f"gluster volume add-brick {self.vol_name} "
               f"{' '.join(nested_bricks_list)}")
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0], False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: Add-brick is successfull")
        err_msg = ("Brick may be containing or be contained by an existing"
                   " brick")
        if err_msg not in ret['error_msg']:
            raise Exception("Unexpected: add-brick is successful without any"
                            " error")

        # Case 4: test_add_brick_non_existent_volume
        """Test add-bricks to an non existent volume"""
        # Form bricks list for add-brick
        brick_cmd = redant.form_brick_cmd_to_add_brick(self.server_list[0],
                                                       self.vol_name,
                                                       self.server_list,
                                                       self.brick_roots)
        cmd = f"gluster volume add-brick novolume {brick_cmd}"
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0], False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: Add-brick is successfull")
        err_msg1 = "does not exist"
        err_msg2 = "Unable to get volinfo for volume name novolume"
        if err_msg1 not in ret['error_msg'] \
           or err_msg2 not in ret['error_msg']:
            raise Exception("Unexpected: add-brick is successful without any"
                            " error")

        # Case 5: test_add_brick_peer_not_in_cluster
        """
        Test add bricks to the volume from the host which is not
        in the cluster.
        """
        # Form bricks list for add-brick
        bricks_list = redant.get_subvols(self.vol_name,
                                         self.server_list[0])[0]
        for (i, item) in enumerate(bricks_list):
            server, _ = item.split(":")
            item.replace(server, "abc.def.ghi.jkl")
            bricks_list[i] = item.replace(server, "abc.def.ghi.jkl")

        brick_str = " ".join(bricks_list)
        ret = redant.add_brick(self.vol_name, brick_str, self.server_list[0],
                               excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: add-brick is successful")
        err_msg = "Pre-validation failed on localhost"
        if err_msg not in ret['msg']['opErrstr']:
            raise Exception("Unexpected: add-brick successful without "
                            "any error")
