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
"""

# nonDisruptive;
from tests.nd_parent_test import NdParentTest


class TestGlusterdInfo(NdParentTest):

    def run_test(self, redant):
        """
        test_glusterd_config_file_check test function is merged with
        test_validate _glusterd_info test function.
        Steps:
            1. Check for the presence of /var/lib/glusterd/glusterd.info file
            2. Get the UUID of the current NODE
            3. check the value of the uuid returned by executing the command -
                "gluster system:: uuid get "
            4. Check the uuid value shown by other node in the cluster
                for the same node "gluster peer status"
                on one node will give the UUID of the other node
            5. Check the location of glusterd socket file ( glusterd.socket )
                ls  /var/run/ | grep -i glusterd.socket
            6. systemctl is-enabled glusterd -> enabled
        """
        # Skip if upstream installation
        self.redant.check_gluster_installation(self.server_list, "downstream")

        for server in self.server_list:

            # Getting UUID from glusterd.info
            redant.logger.info("Getting the UUID from glusterd.info")
            ret = redant.execute_abstract_op_node("grep -i uuid /var/lib/"
                                                  "glusterd/glusterd.info",
                                                  server)
            glusterd_volinfo = " ".join(ret['msg'])
            glusterd_volinfo = (glusterd_volinfo.split("="))[1]
            if not glusterd_volinfo:
                raise Exception("UUID not found in 'glusterd.info' file ")

            # Getting UUID from cmd 'gluster system uuid get'
            ret = redant.execute_abstract_op_node("gluster system:: uuid get |"
                                                  " awk {'print $2'}", server)
            get_uuid = " ".join(ret['msg'])
            if not get_uuid:
                raise Exception("UUID not found")

            # Checking if both the uuid are same
            if glusterd_volinfo != get_uuid:
                raise Exception(f"UUID does not match in host{server}")

            # Geting the UUID from cmd "gluster peer status"
            for node in self.server_list:
                uuid_list = []
                if node != server:
                    peer_status_list = redant.get_peer_status(node)
                    if isinstance(peer_status_list, list):
                        for peer in peer_status_list:
                            uuid_list.append(peer["uuid"])
                    else:
                        uuid_list.append(peer_status_list["uuid"])

                    if get_uuid.rstrip("\n") not in uuid_list:
                        raise Exception(f"uuid not matched in {node}")

        # Merged test_glusterd_config_file_check into this test case
        # TODO: replace the below operation with path_exists function call
        cmd = "ls  /var/run/ | grep -i glusterd.socket"
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0])
        msg = " ".join(ret['msg'])

        # Checking glusterd.socket file
        if msg.replace("\n", "") != "glusterd.socket":
            raise Exception("Failed to get expected output")

        # Checking for glusterd.service is enabled by default
        ret = redant.execute_abstract_op_node(
            "systemctl is-enabled glusterd.service", self.server_list[0])
        msg = " ".join(ret['msg'])
        if msg.replace("\n", "") != 'enabled':
            raise Exception(
                "Output of systemctl is-enabled glusterd.service is"
                " not enabled")
