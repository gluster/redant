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


@runs_on([['replicated', 'distributed-replicated'], ['glusterfs']])
"""
# nonDisruptive;rep

from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):

    def run_test(self, redant):
        """
        - note the current available space on the mount
        - create 1M file on the mount
        - note the current available space on the mountpoint and compare
          with space before creation
        - remove the file
        - note the current available space on the mountpoint and compare
          with space before creation
        """

        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        # Create 1M file on client side
        self.proc = (redant.
                     create_files(num_files=1,
                                  fix_fil_size="1M",
                                  path=self.mounts[0]['mountpath'],
                                  node=self.mounts[0]['client']))
        ret = self.redant.validate_io_procs(self.proc, self.mounts[0])
        if not ret:
            raise Exception("IO validation failed")


        # Get the current available space on the mount
        cmd = (f"df --output=avail {self.mounts[0]['mountpath']}"
               f" | grep '[0-9]'")
        ret = redant.execute_abstract_op_node(cmd,
                                              self.mounts[0]['client'])
        print(ret,"\n")
        # space_before_file_creation = int(out)

        # Create 1M file on client side
        self.proc = (redant.
                     create_files(num_files=1,
                                  fix_fil_size="1M",
                                  path=self.mounts[0]['mountpath'],
                                  node=self.mounts[0]['client'],
                                  base_file_name="newfile"))
        ret = self.redant.validate_io_procs(self.proc, self.mounts[0])
        if not ret:
            raise Exception("IO validation failed")

        # Get the current available space on the mount
        cmd = (f"df --output=avail {self.mounts[0]['mountpath']}"
               f" | grep '[0-9]'")
        ret = redant.execute_abstract_op_node(cmd,
                                              self.mounts[0]['client'])
        print(ret,"\n")
        # space_after_file_creation = int(out)

        # # Compare available size before creation and after creation file
        # g.log.info('Comparing available size before creation '
        #            'and after creation file...')
        # space_diff = space_before_file_creation - space_after_file_creation
        # space_diff = round(space_diff / 1024)
        # g.log.info('Space difference is %d', space_diff)
        # self.assertEqual(space_diff, 1.0,
        #                  'Available size before creation and '
        #                  'after creation file is not valid')
        # g.log.info('Available size before creation and '
        #            'after creation file is valid')

        # # Delete file on client side
        # g.log.info('Deleting file on %s', self.mounts[0].mountpoint)
        # cmd = ("/usr/bin/env python %s delete %s/newdir"
        #        % (self.script_upload_path, self.mounts[0].mountpoint))
        # ret, _, err = g.run(self.mounts[0].client_system, cmd)
        # self.assertFalse(ret, err)

        # # Get the current available space on the mount
        # cmd = ("df --output=avail %s | grep '[0-9]'"
        #        % self.mounts[0].mountpoint)
        # ret, out, err = g.run(self.mounts[0].client_system, cmd)
        # self.assertFalse(ret, err)
        # space_after_file_deletion = int(out)

        # # Compare available size before creation and after deletion file
        # g.log.info('Comparing available size before creation '
        #            'and after deletion file...')
        # space_diff = space_before_file_creation - space_after_file_deletion
        # space_diff_comp = space_diff < 200
        # self.assertTrue(space_diff_comp,
        #                 'Available size before creation is not proportional '
        #                 'to the size after deletion file')
        # g.log.info('Available size before creation is proportional '
        #            'to the size after deletion file')
