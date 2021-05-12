"""
  Copyright (C) 2021 Red Hat, Inc. <http://www.redhat.com>

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
    Test case which destroys a volume of said type.
"""

from tests.lazy_parent_test import LazyParentTest


class VolDestroy(LazyParentTest):

    def run_test(self, redant):
        """
        This child is responsible for the destruction of a volume
        of said type and its mountpoint.
        """
        mountpoint = (f"/mnt/{self.vol_name}")
        redant.volume_unmount(self.vol_name, mountpoint, self.client_list[0])
        redant.execute_io_cmd(f"rm -rf {mountpoint}", self.client_list[0])
        redant.volume_stop(self.vol_name, self.server_list[0], True)
        redant.volume_delete(self.vol_name, self.server_list[0])
