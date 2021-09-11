"""
  Copyright (C) 2018  Red Hat, Inc. <http://www.redhat.com>

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
    Test ec_io_hang_during_serverside_heal
"""
# nonDisruptive;disp,dist-disp

from random import choice
from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):
    def run_test(self, redant):
        """
        1. Disable client side heal.
        2. Perform IO on mount point and kill some bricks and bring them up.
        3. Check that the heal should complete via client side heal and it
        should not hang any IO.
        """
        # disable client side heal
        options = {"disperse.background-heals": 0}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])

        # Log Volume Info and Status after disabling client side heal
        if not (redant.log_volume_info_and_status(self.server_list[0],
                                                  self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Create files
        cmd = (f"cd {self.mountpoint}; mkdir test; cd test; "
               "for i in `seq 1 100` ;"
               "do touch file$i; done;")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Bring bricks offline
        bricks_list = choice(redant.get_all_bricks(
                             self.vol_name, self.server_list[0]))

        redant.bring_bricks_offline(self.vol_name, bricks_list)
        if not redant.are_bricks_offline(self.vol_name, bricks_list,
                                         self.server_list[0]):
            raise Exception(f"Bricks {bricks_list} are"
                            "not offline.")

        # Start pumping IO from client
        cmd = (f"cd {self.mountpoint}; mkdir test; cd test; "
               "for i in `seq 1 100` ;"
               "do dd if=/dev/urandom of=file$i bs=1M "
               "count=5; done;")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Bring bricks online
        redant.bring_bricks_online(self.vol_name, self.server_list[0],
                                   bricks_list)

        # Verifying all bricks online
        if not (redant.are_bricks_online(self.vol_name, bricks_list,
                                         self.server_list[0])):
            raise Exception(f"Bricks {bricks_list} are "
                            "not online.")

        # Start pumping IO from client
        appendcmd = (f"cd {self.mountpoint}; mkdir test; cd test; "
                     "for i in `seq 1 100` ;"
                     "do dd if=/dev/urandom of=file$i bs=1M "
                     "count=1 oflag=append conv=notrunc;done")
        redant.execute_abstract_op_node(appendcmd, self.client_list[0])

        # check the heal info and completion
        self.heal_info = redant.get_heal_info(self.server_list[0],
                                              self.vol_name)
        redant.logger.info(f"Heal Entries {self.vol_name} : {self.heal_info}")
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet finished")

        # Log Volume Info and Status after bringing the brick up
        if not (redant.log_volume_info_and_status(self.server_list[0],
                                                  self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")
