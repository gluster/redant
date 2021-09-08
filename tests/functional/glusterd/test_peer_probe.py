"""
  Copyright (C) 2016-2017  Red Hat, Inc. <http://www.redhat.com>

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
  Validating various cases of peer probe between nodes with
  volume creation on different nodes.
"""
from copy import deepcopy
from time import sleep
from tests.d_parent_test import DParentTest


# disruptive;
class TestCase(DParentTest):

    def run_test(self, redant):
        """
        In this test case:
        1. Create Dist Volume on Node 1
        2. Create Replica Volume on Node 2
        3. Peer Probe N2 from N1(should fail)
        4. Clean All Volumes
        5. Peer Probe N1 to N2(should success)
           Peer Probe N3 to N2(should fail)
        6. Create replica Volume on N1 and N2
        7. Peer probe from N3 to N1(should fail)
        8. Peer probe from N1 to N3(should succeed)
        9. Create replica Volume on N1, N2 and N2
        10.Start Volume
        11. delete volume (should fail)
        12. Stop volume
        13. Clean up all volumes
        """
        # Destroy the cluster environment
        redant.delete_cluster(self.server_list)

        # Create a distributed volume on Node1
        volume_type1 = 'dist'
        volume_name1 = f"{self.test_name}-{volume_type1}-1"
        conf_hash = deepcopy(self.vol_type_inf[volume_type1])
        conf_hash['dist-count'] = 1
        ret = redant.volume_create(volume_name1, self.server_list[0],
                                   conf_hash, self.server_list[0],
                                   self.brick_roots, True)

        # Create a replicate volume on Node2 without force should fail
        volume_type2 = 'rep'
        volume_name2 = f"{self.test_name}-{volume_type2}-2"
        conf_hash = deepcopy(self.vol_type_inf[volume_type2])
        conf_hash['replica_count'] = 2
        ret = redant.volume_create(volume_name2, self.server_list[1],
                                   conf_hash, self.server_list[1],
                                   self.brick_roots, excep=False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: Successfully created "
                            "the replicate volume on node2 "
                            "without force")

        # Create a replica volume on Node2 with force should succeed
        volume_type3 = 'rep'
        volume_name3 = f"{self.test_name}-{volume_type3}-3"
        conf_hash = deepcopy(self.vol_type_inf[volume_type3])
        conf_hash['replica_count'] = 3
        ret = redant.volume_create(volume_name3, self.server_list[1],
                                   conf_hash, self.server_list[1],
                                   self.brick_roots, True)

        # Perform peer probe from N1 to N2
        ret = redant.peer_probe(self.server_list[1], self.server_list[0],
                                False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: peer probe succeeded from "
                            f"{self.server_list[0]} "
                            f"to {self.server_list[1]}")

        # clean up all volumes
        redant.volume_delete(volume_name1, self.server_list[0])
        redant.volume_delete(volume_name3, self.server_list[1])

        # Perform peer probe from N1 to N2 should success
        redant.peer_probe(self.server_list[1], self.server_list[0])

        # Checking if peer is connected
        counter = 0
        while counter < 30:
            ret = redant.is_peer_connected(self.server_list[1],
                                           self.server_list[0])
            counter += 1
            if ret:
                break
            sleep(3)
        if not ret:
            raise Exception("Peer is not in connected state.")

        # Perform peer probe from N3 to N2 should fail
        ret = redant.peer_probe(self.server_list[1], self.server_list[2],
                                False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: peer probe succeeded from "
                            f"{self.server_list[2]} to "
                            f"{self.server_list[1]}")

        # Create a replica volume on N1 and N2 with force
        volume_type4 = 'rep'
        volume_name4 = f"{self.test_name}-{volume_type4}-4"
        conf_hash = deepcopy(self.vol_type_inf[volume_type4])
        conf_hash['replica_count'] = 2
        ret = redant.volume_create(volume_name4, self.server_list[0],
                                   conf_hash, self.server_list[0:2],
                                   self.brick_roots, True)

        # Perform peer probe from N3 to N1 should fail
        ret = redant.peer_probe(self.server_list[0], self.server_list[2],
                                False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: peer probe succeeded from "
                            f"{self.server_list[2]} to "
                            f"{self.server_list[0]}")

        # Perform peer probe from N1 to N3 should succed
        redant.peer_probe(self.server_list[2], self.server_list[0])

        # Checking if peer is connected
        counter = 0
        while counter < 30:
            ret = redant.is_peer_connected(self.server_list[:3],
                                           self.server_list[0])
            counter += 1
            if ret:
                break
            sleep(3)
        if not ret:
            raise Exception("Peer is not in connected state.")

        # Create a replica volume on N1, N2 and N3 with force
        volume_type5 = 'rep'
        volume_name5 = f"{self.test_name}-{volume_type5}-5"
        conf_hash = deepcopy(self.vol_type_inf[volume_type5])
        conf_hash['replica_count'] = 3
        ret = redant.volume_create(volume_name5, self.server_list[0],
                                   conf_hash, self.server_list,
                                   self.brick_roots, True)

        ret = redant.volume_start(volume_name5, self.server_list[2], True)

        # Volume delete should fail without stopping volume
        ret = redant.volume_delete(volume_name5, self.server_list[2], False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: Volume deleted "
                            "successfully without stopping volume")

        # Volume stop with force
        redant.volume_stop(volume_name5, self.server_list[0], True)
