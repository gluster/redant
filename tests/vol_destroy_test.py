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

from .lazy_parent_test import LazyParentTest


class VolDestroy(LazyParentTest):

    def run_test(self, redant):
        """
        This child is responsible for the destruction of a volume
        of said type and its mountpoint.
        """
        redant.cleanup_volume(self.vol_name, self.server_list)
