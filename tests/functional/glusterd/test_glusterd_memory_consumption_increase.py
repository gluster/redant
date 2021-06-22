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
    Increase in glusterd memory consumption on repetetive operations
    for 100 volumes
"""
# disruptive;

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):
    
    # def _volume_operations_in_loop(self):
    #     """ Create, start, stop and delete 100 volumes in a loop """
    #     # Create and start 100 volumes in a loop
    #     self.volume_config = {
    #         'name': 'volume-',
    #         'servers': self.servers,
    #         'voltype': {'type': 'distributed-replicated',
    #                     'dist_count': 2,
    #                     'replica_count': 3},
    #     }

    #     ret = bulk_volume_creation(self.mnode, 100, self.all_servers_info,
    #                                self.volume_config, "", False, True)
    #     self.assertTrue(ret, "Failed to create volumes")

    #     self.volume_present = True

    #     g.log.info("Successfully created all the volumes")

    #     # Start 100 volumes in loop
    #     for i in range(100):
    #         self.volname = "volume-%d" % i
    #         ret, _, _ = volume_start(self.mnode, self.volname)
    #         self.assertEqual(ret, 0, "Failed to start volume: %s"
    #                          % self.volname)

    #     g.log.info("Successfully started all the volumes")

    #     # Stop 100 volumes in loop
    #     for i in range(100):
    #         self.volname = "volume-%d" % i
    #         ret, _, _ = volume_stop(self.mnode, self.volname)
    #         self.assertEqual(ret, 0, "Failed to stop volume: %s"
    #                          % self.volname)

    #     g.log.info("Successfully stopped all the volumes")

    #     # Delete 100 volumes in loop
    #     for i in range(100):
    #         self.volname = "volume-%d" % i
    #         ret = volume_delete(self.mnode, self.volname)
    #         self.assertTrue(ret, "Failed to delete volume: %s"
    #                         % self.volname)

    #     self.volume_present = False

    #     g.log.info("Successfully deleted all the volumes")

    def _memory_consumption_for_all_nodes(self, pid_list):
        """Fetch the memory consumption by glusterd process for
           all the nodes
        """
        memory_consumed_list = []
        for i, server in enumerate(self.server_list):
            # Get the memory consumption of glusterd in each node
            cmd = (f"top -b -n 1 -p {pid_list[i]} | "
                   "awk 'FNR==8 {print $6}'")
            ret = self.redant.execute_abstract_op_node(cmd,
                                                       server,
                                                       False)

            if ret['error_code'] != 0:
                print("Failed to get the memory usage of"
                      " glusterd process")
            mem = 0
            if len(ret['msg']) > 0:
                mem = int((ret['msg'][0]).rstrip("\n"))//1024
            memory_consumed_list.append(mem)

        return memory_consumed_list

    def run_test(self, redant):
        """
        Test Case:
        1) Enable brick-multiplex and set max-bricks-per-process to 3 in
           the cluster
        2) Get the glusterd memory consumption
        3) Perform create,start,stop,delete operation for 100 volumes
        4) Check glusterd memory consumption, it should not increase by
           more than 50MB
        5) Repeat steps 3-4 for two more time
        6) Check glusterd memory consumption it should not increase by
           more than 10MB
        """
        # Restarting glusterd to refresh its memory consumption
        redant.restart_glusterd(self.server_list)
        # check if glusterd is running post reboot
        if not redant.wait_for_glusterd_to_start(self.server_list):
            raise Exception("Glusterd service is not running post reboot")
        
        # Enable brick-multiplex, set max-bricks-per-process to 3 in cluster
        for key, value in (('cluster.brick-multiplex', 'enable'),
                           ('cluster.max-bricks-per-process', '3')):
            redant.set_volume_options('all', {key: value},
                                      self.server_list[0])
            

        cmd = "pidof glusterd"
        # Get the pidof of glusterd process
        pid_list = []
        ret = redant.execute_abstract_op_multinode(cmd,
                                                   self.server_list)

        for result in ret:
            pid_list.append(int(result['msg'][0].rstrip("\n")))

        # Fetch the list of memory consumed in all the nodes
        mem_consumed_list = (self.
                             _memory_consumption_for_all_nodes(pid_list))
        print(f"Mem: \n{mem_consumed_list}")

        # # Perform volume operations for 100 volumes for first time
        # self._volume_operations_in_loop()

        # # Fetch the list of memory consumed in all the nodes after 1 iteration
        # mem_consumed_list_1 = self._memory_consumption_for_all_nodes(pid_list)

        # for i, mem in enumerate(mem_consumed_list_1):
        #     condition_met = False
        #     if mem - mem_consumed_list[i] <= 50:
        #         condition_met = True

        #     self.assertTrue(condition_met, "Unexpected: Memory consumption"
        #                     " glusterd increased more than the expected"
        #                     " of value")

        # # Perform volume operations for 100 volumes for second time
        # self._volume_operations_in_loop()

        # # Fetch the list of memory consumed in all the nodes after 2 iterations
        # mem_consumed_list_2 = self._memory_consumption_for_all_nodes(pid_list)

        # for i, mem in enumerate(mem_consumed_list_2):
        #     condition_met = False
        #     if mem - mem_consumed_list_1[i] <= 10:
        #         condition_met = True

        #     self.assertTrue(condition_met, "Unexpected: Memory consumption"
        #                     " glusterd increased more than the expected"
        #                     " of value")

        # # Perform volume operations for 100 volumes for third time
        # self._volume_operations_in_loop()

        # # Fetch the list of memory consumed in all the nodes after 3 iterations
        # mem_consumed_list_3 = self._memory_consumption_for_all_nodes(pid_list)

        # for i, mem in enumerate(mem_consumed_list_3):
        #     condition_met = False
        #     if mem - mem_consumed_list_2[i] <= 10:
        #         condition_met = True

        #     self.assertTrue(condition_met, "Unexpected: Memory consumption"
        #                     " glusterd increased more than the expected"
        #                     " of value")
