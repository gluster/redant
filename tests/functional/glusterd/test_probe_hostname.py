"""
Copyright (C) 2017-2018  Red Hat, Inc. <http://www.redhat.com>

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

This test deals with testing peer probe
using hostnames.
"""

import socket
from tests.d_parent_test import DParentTest

# disruptive;


class TestCase(DParentTest):

    def _vol_operations(self, redant, volname: str):
        """
        This function performs a
        set of colume operations like
        start, volume status, info,
        volume delete.
        """

        # Start a volume
        redant.volume_start(volname, self.server_list[0])
        redant.logger.info(f"Volume: {volname} started successfully")

        # Get volume info
        volinfo = redant.get_volume_info(self.server_list[0], volname)
        if volinfo is None:
            raise Exception(f"Failed to get volume info of {volname}")
        redant.logger.info(f"Vol info: {volinfo}")

        # Get volume status
        vol_status = redant.get_volume_status(volname,
                                              self.server_list[0])
        if vol_status is None:
            raise Exception(f"Failed to get volume status of {volname}")
        redant.logger.info(f"Vol status: {vol_status}")

        # stop volume
        redant.volume_stop(volname, self.server_list[0], True)

        # delete the volume
        redant.volume_delete(volname, self.server_list[0])

    def run_test(self, redant):
        '''
        -> Create trusted storage pool, by probing with networkshort names
        -> Create volume using IP of host
        -> perform basic operations like
            -> gluster volume start <vol>
            -> gluster volume info <vol>
            -> gluster volume status <vol>
            -> gluster volume stop <vol>
        -> Create a volume using the FQDN of the host
        -> perform basic operations like
            -> gluster volume start <vol>
            -> gluster volume info <vol>
            -> gluster volume status <vol>
            -> gluster volume stop <vol>
        '''

        # detaching all the peers first
        for server in self.server_list[1:]:
            redant.peer_detach(server, self.server_list[0], True)

        redant.logger.info("Peer detach successfull")

        # Peer probing using short name
        for server in self.server_list[1:]:
            ret = redant.execute_abstract_op_node("hostname -s", server)
            hostname = ret['msg'][0].rstrip('\n')

            redant.peer_probe(hostname, self.server_list[0], False)

            if ret['error_code'] != 0:
                ret = redant.execute_abstract_op_node("hostname",
                                                      server)
                hostname = ret['msg'][0].rstrip('\n')
                hostname = hostname.split(".")[0]+"."+hostname.split(".")[1]
                ret = redant.peer_probe(hostname, self.server_list[0],
                                        False)

                if ret['error_code'] != 0:
                    raise Exception(f"Unable to peer probe to"
                                    f" the server {hostname}")

            redant.logger.info(f"Peer probe succeeded for {hostname}")

        # Create a volume
        redant.volume_create("test-vol", self.server_list[0],
                             self.vol_type_inf[self.conv_dict['dist']],
                             self.server_list, self.brick_roots, True)

        redant.logger.info("Volume: test-vol created successfully")

        # perform the set of volume operations
        self._vol_operations(redant, "test-vol")

        # Getting FQDN (Full qualified domain name) of each host and
        # replacing ip with FQDN name for each brick for example
        # 10.70.37.219:/bricks/brick0/vol1 is a brick, here ip is replaced
        # with FQDN name now brick looks like
        # dhcp35-219.lab.eng.blr.redhat.com:/bricks/brick0/vol1
        brick_dict, brick_cmd = redant.form_brick_cmd(self.server_list,
                                                      self.brick_roots,
                                                      "test-vol-fqdn", 3)
        brick_list = brick_cmd.split()
        fqdn_brick_cmd = ""

        for brick in brick_list:
            fqdn_list = brick.split(":")
            fqdn = socket.getfqdn(fqdn_list[0])
            fqdn = f"{fqdn}:{fqdn_list[1]}"
            fqdn_brick_cmd = f"{fqdn_brick_cmd} {fqdn}"

        # create a volume
        cmd = f"gluster vol create test-vol-fqdn{fqdn_brick_cmd} force"
        redant.execute_abstract_op_node(cmd, self.server_list[0])
        redant.es.set_new_volume("test-vol-fqdn", brick_dict)

        # perform the set of volume operations
        self._vol_operations(redant, "test-vol-fqdn")

        # creating the cluster back again
        ret = redant.create_cluster(self.server_list)

        if not ret:
            raise Exception("Cluster creation failed")
