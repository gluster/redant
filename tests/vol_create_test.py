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
    Test case which creates a volume of said type.
"""

from .lazy_parent_test import LazyParentTest


class VolCreate(LazyParentTest):

    def run_test(self, redant):
        """
        This child is responsible for the creation of a volume
        of said type so that tests can use it.
        """
        vol_param = self.vol_type_inf[self.volume_type]
        redant.volume_create(self.vol_name, self.server_list[0], vol_param,
                             self.server_list, self.brick_roots, True)
        redant.volume_start(self.vol_name, self.server_list[0])
        redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                        self.client_list[0])
        redant.volume_mount(self.server_list[0], self.vol_name,
                            self.mountpoint, self.client_list[0])
