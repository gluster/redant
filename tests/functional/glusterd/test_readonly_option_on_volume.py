"""
Copyright (C) 2018-2020  Red Hat, Inc. <http://www.redhat.com>

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
"""


from tests.nd_parent_test import NdParentTest

# nonDisruptive;dist,rep,dist-rep,disp,dist-disp

class TestCase(NdParentTest):
    def run_test(self):
        '''
        -> Create volume
        -> Mount a volume
        -> set 'read-only on' on a volume
        -> perform some I/O's on mount point
        -> set 'read-only off' on a volume
        -> perform some I/O's on mount point
        '''

        # Setting Read-only on volume
        ret = set_volume_options(self.mnode, self.volname,{'read-only': 'on'})

        # run IOs
        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            cmd = ("/usr/bin/env python %s create_deep_dirs_with_files ""--dirname-start-num %d ""--dir-depth 2 ""--dir-length 2 ""--max-num-of-dirs 2 ""--num-of-files 5 %s" % (self.script_upload_path,self.counter,mount_obj.mountpoint))

            proc = g.run_async(mount_obj.client_system, cmd,user=mount_obj.user)
            self.all_mounts_procs.append(proc)
            self.counter = self.counter + 10

        # Validate IO

        # Setting Read only off volume
        ret = set_volume_options(self.mnode, self.volname,{'read-only': 'off'})

        # run IOs
        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            cmd = ("/usr/bin/env python %s create_deep_dirs_with_files ""--dirname-start-num %d ""--dir-depth 2 ""--dir-length 2 ""--max-num-of-dirs 2 ""--num-of-files 5 %s" % (self.script_upload_path,self.counter,mount_obj.mountpoint))

            proc = g.run_async(mount_obj.client_system, cmd,user=mount_obj.user)
            self.all_mounts_procs.append(proc)
            self.counter = self.counter + 10

        # Validate IO
