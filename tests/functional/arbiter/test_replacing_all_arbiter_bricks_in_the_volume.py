"""
Copyright (C) 2015-2020  Red Hat, Inc. <http://www.redhat.com>

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
    Arbiter Test cases related to
    healing in default configuration of the volume

from glusto.core import Glusto as g

from glustolibs.gluster.gluster_base_class import (GlusterBaseClass, runs_on)
from glustolibs.gluster.exceptions import ExecutionError
from glustolibs.gluster.volume_libs import (
    verify_all_process_of_volume_are_online,
    wait_for_volume_process_to_be_online,
    get_subvols)
from glustolibs.gluster.brick_libs import get_all_bricks
from glustolibs.gluster.brick_ops import replace_brick
from glustolibs.gluster.heal_libs import (monitor_heal_completion,
                                          is_heal_complete,
                                          is_volume_in_split_brain,
                                          is_shd_daemonized)
from glustolibs.misc.misc_libs import upload_scripts
from glustolibs.io.utils import (validate_io_procs,
                                 list_all_files_and_dirs_mounts,
                                 wait_for_io_to_complete)


@runs_on([['distributed-arbiter'],
          ['glusterfs']])
"""

# disruptive;dist-arb

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def test_replacing_all_arbiters(self):
        """
        - Create an arbiter volume 4(2+1) distributed replicate
        - Start writing IO
        - While the I/O's are going on replace all the arbiter bricks
        - check for the new bricks attached successfully
        - Check for heals
        - Validate IO
        """
        # get the bricks for the volume
        self.all_mounts_procs = []
        self.bricks_to_clean = []
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        if bricks_list is None:
            raise Exception("Bricks list is none")

        # # Clear all brick folders. Its need to prevent healing with old files
        # for brick in bricks_list:
        #     g.log.info('Clearing brick %s', brick)
        #     node, brick_path = brick.split(':')
        #     ret, _, err = g.run(node, 'cd %s/ ; rm -rf *' % brick_path)
        #     self.assertFalse(ret, err)
        #     g.log.info('Clearing brick %s is successful', brick)
        # g.log.info('Clearing for all brick is successful')

        # # Creating files on client side
        # for mount_obj in self.mounts:
        #     g.log.info("Generating data for %s:%s",
        #                mount_obj.client_system, mount_obj.mountpoint)
        #     # Create dirs with file
        #     g.log.info('Creating dirs with file...')
        #     command = ("/usr/bin/env python %s create_deep_dirs_with_files "
        #                "-d 3 -l 3 -n 3 -f 20 %s"
        #                % (self.script_upload_path, mount_obj.mountpoint))

        #     proc = g.run_async(mount_obj.client_system, command,
        #                        user=mount_obj.user)
        #     self.all_mounts_procs.append(proc)
        # self.io_validation_complete = False

        # # replace bricks
        # subvols = get_subvols(self.mnode, self.volname)['volume_subvols']
        # for subvol in subvols:
        #     g.log.info('Replacing arbiter brick for %s', subvol)
        #     brick_to_replace = subvol[-1]
        #     self.bricks_to_clean.append(brick_to_replace)
        #     new_brick = brick_to_replace + 'new'
        #     g.log.info("Replacing the brick %s for the volume: %s",
        #                brick_to_replace, self.volname)
        #     ret, _, err = replace_brick(self.mnode, self.volname,
        #                                 brick_to_replace, new_brick)
        #     self.assertFalse(ret, err)
        #     g.log.info('Replaced brick %s to %s successfully',
        #                brick_to_replace, new_brick)

        # # check replaced bricks
        # subvols = get_subvols(self.mnode, self.volname)['volume_subvols']
        # index = 0
        # for subvol in subvols:
        #     expected_brick_path = self.bricks_to_clean[index]+'new'
        #     brick_to_check = subvol[-1]
        #     self.assertEqual(expected_brick_path, brick_to_check,
        #                      'Brick %s is not replaced brick'
        #                      % brick_to_check)
        #     index += 1

        # # Wait for volume processes to be online
        # g.log.info("Wait for volume processes to be online")
        # ret = wait_for_volume_process_to_be_online(self.mnode, self.volname)
        # self.assertTrue(ret, ("Failed to wait for volume %s processes to "
        #                       "be online", self.volname))
        # g.log.info("Successful in waiting for volume %s processes to be "
        #            "online", self.volname)

        # # Verify volume's all process are online
        # g.log.info("Verifying volume's all process are online")
        # ret = verify_all_process_of_volume_are_online(self.mnode,
        #                                               self.volname)
        # self.assertTrue(ret, ("Volume %s : All process are not online"
        #                       % self.volname))
        # g.log.info("Volume %s: All process are online", self.volname)

        # # Wait for self-heal-daemons to be online
        # g.log.info("Waiting for self-heal-daemons to be online")
        # ret = is_shd_daemonized(self.all_servers)
        # self.assertTrue(ret, "Either No self heal daemon process found")
        # g.log.info("All self-heal-daemons are online")

        # # Monitor heal completion
        # ret = monitor_heal_completion(self.mnode, self.volname)
        # self.assertTrue(ret, 'Heal has not yet completed')

        # # Check if heal is completed
        # ret = is_heal_complete(self.mnode, self.volname)
        # self.assertTrue(ret, 'Heal is not complete')
        # g.log.info('Heal is completed successfully')

        # # Check for split-brain
        # ret = is_volume_in_split_brain(self.mnode, self.volname)
        # self.assertFalse(ret, 'Volume is in split-brain state')
        # g.log.info('Volume is not in split-brain state')

        # # Validate IO
        # ret = validate_io_procs(self.all_mounts_procs, self.mounts)
        # self.assertTrue(ret, "IO failed on some of the clients")
        # self.io_validation_complete = True
