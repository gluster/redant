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
    TC to check git clone on client on multiple directories
    with performance options set to OFF
"""

# disruptive;rep,dist-rep,disp,dist-disp,arb,dist-arb

from tests.d_parent_test import DParentTest


class TestGitCloneOnGlusterVolume(DParentTest):

    def _run_git_clone(self, options):
        """Run git clone on the client"""

        repo = "https://github.com/gluster/glusterfs.git"
        cloned_repo_dir = (f"{self.mountpoint}/"
                           f"{repo.split('/')[-1].rstrip('.git')}")
        if options:
            cloned_repo_dir = (f"{self.mountpoint}/perf-"
                               f"{repo.split('/')[-1].rstrip('.git')}")

        cmd = f"cd /root; git clone {repo} {cloned_repo_dir}"
        ret = self.redant.execute_abstract_op_node(cmd, self.client_list[0],
                                                   False)
        if ret['error_code'] != 0:
            self.redant.logger.error("Cloning repo failed on "
                                     f"{self.client_list[0]}")
            raise Exception(f"Unable to clone {repo} repo on "
                            f"{cloned_repo_dir}")
        else:
            self.redant.logger.info("Successfully cloned repo on "
                                    f"{self.client_list[0]}")

    def run_test(self, redant):
        """
        Test Steps:
        1. Create a volume and mount it on one client
        2. git clone the glusterfs repo on the glusterfs volume.
        3. Set the performance options to off
        4. Repeat step 2 on a different directory.
        """
        self._run_git_clone(False)

        # Disable the performance cache options on the volume
        options = {'performance.quick-read': 'off',
                   'performance.stat-prefetch': 'off',
                   'performance.open-behind': 'off',
                   'performance.write-behind': 'off',
                   'performance.client-io-threads': 'off'}
        redant.set_volume_options(self.vol_name, options, self.server_list[0],
                                  multi_option=True)

        self._run_git_clone(True)
