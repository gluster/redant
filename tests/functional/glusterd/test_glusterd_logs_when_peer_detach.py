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

  Description:
        No Errors should generate in glusterd.log while detaching
        node from gluster
"""

import random
from tests.abstract_test import AbstractTest

# disruptive;


class GlusterdLogsWhilePeerDetach(AbstractTest):

    def run_test(self, redant):
        '''
            1) Detach the node from peer
            2) Check that any error messages related to peer detach
                in glusterd log file
            3) No errors should be there in glusterd log file
        '''

        # Getting timestamp
        ret = redant.execute_abstract_op_node('date +%s', self.server_list[0])
        timestamp = ret['msg'][0].rstrip("\n")

        #  glusterd logs
        ret = redant.execute_abstract_op_node('cp /var/log/glusterfs/glusterd.log /var/'
                                    f'log/glusterfs/glusterd_{timestamp}.log',
                                    self.server_list[0])

        # Clearing the existing glusterd log file
        ret = redant.execute_abstract_op_node('echo > /var/log/glusterfs/glusterd.log',
                                    self.server_list[0])

        # Performing peer detach
        random_server = random.choice(self.server_list[1:])
        ret = redant.peer_detach(random_server, self.server_list[0])

        # Searching for error message in log
        ret = redant.execute_abstract_op_node("grep ' E ' /var/log/glusterfs/"
                                    "glusterd.log | wc -l",
                                    self.server_list[0])
        if int(ret['msg'][0]) != 0:
            redant.logger.info("Found Error messages in glusterd log "
                               "file after peer detach")
