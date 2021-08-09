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
This test checks if gluster does not do posix lock
when multiple clients are present.
"""

from tests.nd_parent_test import NdParentTest

# nonDisruptive;dist,rep,dist-rep,disp,dist-disp,arb,dist-arb


class TestCase(NdParentTest):

    def run_test(self, redant):
        """
        Steps:
        1. Create all types of volumes.
        2. Mount the brick on two client mounts
        3. Prepare same script to do flock on the two nodes
         while running this script it should not hang
        4. Wait till 300 iteration on both the node
        """
        # Check client requirements
        redant.check_hardware_requirements(self.client_list, 2)

        # Shell Script to be run on mount point
        script = """
                #!/bin/bash
                flock_func(){
                file=/bricks/brick0/test.log
                touch $file
                (
                         flock -xo 200
                         echo "client1 do something" > $file
                         sleep 1
                 ) 300>$file
                }
                i=1
                while [ "1" = "1" ]
                do
                    flock_func
                    ((i=i+1))
                    echo $i
                    if [[ $i == 300 ]]; then
                            break
                    fi
                done
                """
        mount_point = redant.es.get_mnt_pts_list(self.vol_name,
                                                 self.client_list[0])[0]
        cmd = f"echo {script} >{mount_point}/test.sh; sh {mount_point}/test.sh"
        ret = redant.execute_abstract_op_multinode(cmd,
                                                   self.client_list[:2],
                                                   False)
        # Check if 300 is present in the output
        for item in ret:
            if item['error_code'] == 0:
                out = item['msg']
                if "300\n" not in out:
                    raise Exception(f"Failed to run the command on "
                                    f"{item['node']}")
            else:
                raise Exception(f"Failed to execute the script: "
                                f"{item['error_msg']}")
