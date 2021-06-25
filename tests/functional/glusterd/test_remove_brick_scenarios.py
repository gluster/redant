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

You should have received a copy of the GNU General Public License along`
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

Description:

This test deals with scenarios with remove brick
functionality.

"""
# disruptive;dist-rep

from multiprocessing.pool import ThreadPool
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Test case:
        1. Create a cluster by peer probing and create a volume.
        2. Mount it and write some IO like 100000 files.
        3. Initiate the remove-brick operation on pair of bricks.
        4. Stop the remove-brick operation using other pairs of bricks.
        5. Get the remove-brick status using other pair of bricks in
           the volume.
        6. stop the rebalance process using non-existing brick.
        7. Check for the remove-brick status using non-existent bricks.
        8. Stop the remove-brick operation where remove-brick start have been
            initiated.
        9. Perform fix-layout on the volume.
        10. Get the rebalance fix-layout.
        11. Create a directory from mountpoint.
        12. check for 'trusted.glusterfs.dht' extended attribute in the
            newly created directory in the bricks where remove brick stopped
            (which was tried to be removed in step 8).
        13. Umount, stop and delete the volume.
        """
        # Getting a list of all the bricks.
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        if bricks_list is None:
            raise Exception("Error: Couldn't fetch the bricks list")

        # Running IO.
        pool = ThreadPool(5)
        # Build a command per each thread
        # e.g. "seq 1 20000 ... touch" , "seq 20001 40000 ... touch" etc
        cmds = [f"seq {i} {i + 19999} | sed 's|^|{self.mountpoint}/"
                f"test_file|' | xargs touch"
                for i in range(1, 100000, 20000)]
        # Run all commands in parallel
        ret = pool.map(
            lambda command: (redant.
                             execute_abstract_op_node(command,
                                                      self.client_list[0],
                                                      False)), cmds)
        # ret -> list of tuples [(return_code, stdout, stderr),...]
        pool.close()
        pool.join()
        # Verify all commands' exit code is 0 (first element of each tuple)
        for thread_return in ret:
            if thread_return['error_code'] != 0:
                raise Exception("File creation failed.")

        # Removing bricks from volume.
        remove_brick_list_original = bricks_list[3:6]
        redant.remove_brick(self.server_list[0], self.vol_name,
                            remove_brick_list_original, 'start')

        # Stopping brick remove operation for other pair of bricks.
        remove_brick_list_other_pair = bricks_list[0:3]
        ret = redant.remove_brick(self.server_list[0], self.vol_name,
                                  remove_brick_list_other_pair,
                                  'stop', excep=False)

        if ret['msg']['opRet'] == 0:
            raise Exception("Error: Remove brick operation stopped"
                            " on other pair of bricks")

        # Checking status of brick remove operation for other pair of bricks.
        ret = redant.remove_brick(self.server_list[0], self.vol_name,
                                  remove_brick_list_other_pair, 'status',
                                  excep=False)
        if ret['msg']['opRet'] == 0:
            raise Exception("Error: Got status on other pair of bricks.")

        # Stopping remove operation for non-existent bricks.
        remove_brick_list_non_existent = [f"{bricks_list[0]}non-existent",
                                          f"{bricks_list[1]}non-existent",
                                          f"{bricks_list[2]}non-existent"]
        ret = redant.remove_brick(self.server_list[0], self.vol_name,
                                  remove_brick_list_non_existent, 'stop',
                                  excep=False)

        if ret['msg']['opRet'] == 0:
            raise Exception("Error: Successfully stopped remove brick"
                            " operation on non-existent bricks.")

        # # Checking status of brick remove opeation for non-existent bricks.
        ret = redant.remove_brick(self.server_list[0], self.vol_name,
                                  remove_brick_list_non_existent, 'status',
                                  excep=False)
        if ret['msg']['opRet'] == 0:
            raise Exception("Error: Got status on non-existent"
                            " pair of bricks.")

        # Stopping the initial brick remove opeation.
        redant.remove_brick(self.server_list[0], self.vol_name,
                            remove_brick_list_original, 'stop')

        # Start rebalance fix layout for volume.
        redant.rebalance_start(self.vol_name,
                               self.server_list[0],
                               fix_layout=True)

        # Checking status of rebalance fix layout for the volume.
        redant.get_rebalance_status(self.vol_name, self.server_list[0])
        if not redant.wait_for_fix_layout_to_complete(self.server_list[0],
                                                      self.vol_name,
                                                      timeout=30000):
            raise Exception("Failed to check for rebalance")

        # Creating directory.
        dir_name = ''
        for counter in range(0, 10):
            ret = redant.create_dir(self.mountpoint, f"dir1{str(counter)}",
                                    self.client_list[0], False)
            if ret['error_code'] == 0:
                dir_name = f"/dir1{str(counter)}"
                break

        # Checking value of attribute for dht.
        brick_server, brick_dir = bricks_list[0].split(':')
        dir_name = f"{brick_dir}{dir_name}"
        redant.get_fattr(dir_name, 'trusted.glusterfs.dht', brick_server)
