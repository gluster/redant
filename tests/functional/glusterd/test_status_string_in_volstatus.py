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
      Verifying task type and task status in volume status and volume
      status xml
"""

from tests.nd_parent_test import NdParentTest

# nonDisruptive;dist-rep


class TestCase(NdParentTest):

    def run_test(self, redant):
        """
        1) Create Volume
        2) Start rebalance
        3) Check task type in volume status
        4) Check task status string in volume status
        5) Check task type in volume status xml
        6) Check task status string in volume status xml
        7) Start Remove brick operation
        8) Check task type in volume status
        9) Check task status string in volume status
        10) Check task type in volume status xml
        11) Check task status string in volume status xml
        """

        # Start rebalance
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Wait for rebalance to complete
        if not (redant.wait_for_rebalance_to_complete(self.vol_name,
                                                      self.server_list[0])):
            raise Exception("Rebalance operation has not completed."
                            "Wait Timeout")

        # Getting volume status --xml after rebalance start
        vol_status = redant.get_volume_status(self.vol_name,
                                              self.server_list[0],
                                              options='tasks')

        task_status = vol_status[self.vol_name]['task_status'][0]

        # Verifying task type  from volume status --xml for rebalance
        if task_status['type'] != "Rebalance":
            raise Exception("Incorrect task type found in volume status xml "
                            f"for {self.vol_name}")

        # Verifying task status string from volume status --xml for rebalance
        if task_status['statusStr'] != "completed":
            raise Exception("Incorrect task status found in volume status "
                            f"xml for {self.vol_name}")

        # Getting sub vols
        subvol_list = redant.get_subvols(self.vol_name, self.server_list[0])
        subvol = subvol_list[1]

        # Perform remove brick start
        redant.remove_brick(self.server_list[0], self.vol_name, subvol,
                            'start', replica_count=3)

        # Getting volume status --xml after remove brick start
        vol_status = redant.get_volume_status(self.vol_name,
                                              self.server_list[0],
                                              options='tasks')

        # Verifying task type  from volume status --xml after
        # remove brick start
        task_status = vol_status[self.vol_name]['task_status'][0]
        if task_status['type'] != 'Remove brick':
            raise Exception("Incorrect task type found in volume status "
                            f"xml for {self.vol_name}")

        # Verifying task status string from volume status --xml
        # after remove brick start
        remove_status = ['completed', 'in progress']
        ret = False
        if task_status['statusStr'] in remove_status:
            ret = True

        if not ret:
            raise Exception("Incorrect task status found in volume status "
                            f"xml for {self.vol_name}")
