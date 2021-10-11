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
    TC to check consistency in timestamp feature
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp,arb,dist-arb
from re import sub
from tests.d_parent_test import DParentTest


class TestValidateCtimeFeatures(DParentTest):

    def _validate_xattr_values(self, dirname, ctime=True):
        """
        Validate existence and consistency of a specific
        xattr value across replica set
        """
        # Fetch all replica sets(subvols) in the volume
        ret = self.redant.get_subvols(self.vol_name, self.server_list[0])

        # Iterating through each subvol(replicaset)
        for subvol in ret:
            brick_host_list = {}
            for each in subvol:
                # Splitting to brick,hostname pairs
                host, brick_path = each.split(':')
                brick_host_list[host] = brick_path

            # Fetch Complete parent directory path
            directory = f"{brick_path}/{dirname}"

            # Fetching all entries recursively in a replicaset
            entry_list = self.redant.get_dir_contents(directory, host, True)
            for each in entry_list:
                xattr_value = []
                # Logic to get xattr values
                for host, brickpath in brick_host_list.items():
                    # Remove the prefix brick_path from entry-name
                    each = sub(brick_path, '', each)
                    # Adding the right brickpath name for fetching xattrval
                    brick_entry_path = brickpath + each
                    ret = (self.redant.get_extended_attributes_info(host,
                           [brick_entry_path],
                           attr_name='trusted.glusterfs.mdata'))
                    if ret:
                        ret = ret[brick_entry_path]['trusted.glusterfs.mdata']

                    if ctime:
                        if ret is None:
                            raise Exception("glusterfs.mdata not set on"
                                            f"{brick_entry_path}")
                    else:
                        if ret is not None:
                            raise Exception("trusted.glusterfs.mdata seen "
                                            f" on {brick_entry_path}")

                    xattr_value.append(ret)
                voltype = (self.redant.get_volume_type_info(
                           self.server_list[0], self.vol_name))
                if voltype['volume_type_info']['arbiterCount'] == '0':
                    ret = bool(xattr_value.count(xattr_value[0])
                               == len(xattr_value))
                elif voltype['volume_type_info']['arbiterCount'] == '1':
                    ret = bool(((xattr_value.count(xattr_value[0]))
                               or (xattr_value.count(xattr_value[1])) > 1))
                else:
                    self.redant.logger.error("Arbiter value is none of 0, 1")

                if ctime:
                    if not ret:
                        raise Exception('trusted.glusterfs.mdatavalue not '
                                        'across bricks for entry '
                                        f'{each}')
                else:
                    if not ret:
                        raise Exception('trusted.glusterfs.mdata seems to be '
                                        f'set on some bricks for {each}')

    def _data_create(self, dirname):
        """Create different files and directories"""
        dirname = f"{self.mountpoint}/{dirname}"
        list_of_fops = ["create", "rename", "chmod", "chown", "chgrp",
                        "hardlink", "truncate", "setxattr"]
        for fops in list_of_fops:
            ret = self.redant.run_crefi(self.client_list[0],
                                        dirname, 8, 2, 2, thread=4,
                                        random_size=True, fop=fops, minfs=0,
                                        maxfs=10240, multi=True,
                                        random_filename=True)
            if not ret:
                raise Exception(f"crefi failed during {fops}")

    def _data_delete(self, dirname):
        """Delete created data"""
        dirname = f"{self.mountpoint}/{dirname}"
        ret = self.redant.rmdir(dirname, self.client_list[0], force=True)
        if not ret:
            raise Exception('deletion of data failed')

    def run_test(self, redant):
        '''
        Test Steps:
        1. Create a volume, enable features.ctime, mount volume
        2. Create different files and directories
        3. For each entry trusted.glusterfs.mdata  must be set
        4. For every entry, above xattr must match on each brick of replicaset
        5. Delete all data created
        6. turn off features.ctime
        7. Again create different files and directories
        8. "glusterfs.mdata xattr" must not be present for any entry
        9. Delete created data
        '''
        # Enable features.ctime
        redant.set_volume_options(self.vol_name, {'features.ctime': 'on'},
                                  self.server_list[0])

        # Create different files and directories
        self._data_create('ctime-on')

        # Check if mdata xattr has been set for all entries
        # Check if the values are same across all replica copies
        self._validate_xattr_values('ctime-on')

        # Delete all the existing data
        self._data_delete('ctime-on')

        # Disable features.ctime
        redant.set_volume_options(self.vol_name, {'features.ctime': 'off'},
                                  self.server_list[0])

        # Create different files and directories
        self._data_create('ctime-off')

        # Check that mdata xattr has not been set for any entries
        self._validate_xattr_values('ctime-off', ctime=False)

        # Delete all the existing data
        self._data_delete('ctime-off')
