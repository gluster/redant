#  Copyright (C) 2017-2018  Red Hat, Inc. <http://www.redhat.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along`
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


@runs_on([['distributed-replicated'], ['glusterfs']])
class TestVolumeReduceReplicaCount(GlusterBaseClass):

    def test_volume_reduce_replica_count(self):
        """
        Test case:
        1) Create a 2x3 replica volume.
        2) Remove bricks in the volume to make it a 2x2 replica volume.
        3) Remove bricks in the volume to make it a distribute volume.
        """

        # Create and start a volume
        ret = setup_volume(self.mnode, self.all_servers_info, self.volume)
        self.assertTrue(ret, "Failed to create and start volume")

        # Getting a list of all the bricks.
        g.log.info("Get all the bricks of the volume")
        self.brick_list = get_all_bricks(self.mnode, self.volname)
        self.assertIsNotNone(self.brick_list, "Failed to get the brick list")
        g.log.info("Successfully got the list of bricks of volume")

        # Converting 2x3 to 2x2 volume.
        remove_brick_list = [self.brick_list[0], self.brick_list[3]]
        ret, _, _ = remove_brick(self.mnode, self.volname, remove_brick_list,
                                 'force', replica_count=2)
        self.assertEqual(ret, 0, "Failed to start remove brick operation")
        g.log.info("Remove brick operation successfully")

        # Checking if volume is 2x2 or not.
        volume_info = get_volume_info(self.mnode, self.volname)
        brick_count = int(volume_info[self.volname]['brickCount'])
        self.assertEqual(brick_count, 4, "Failed to remove 2 bricks.")
        g.log.info("Successfully removed 2 bricks.")
        type_string = volume_info[self.volname]['typeStr']
        self.assertEqual(type_string, 'Distributed-Replicate',
                         "Convertion to 2x2 failed.")
        g.log.info("Convertion to 2x2 successful.")

        # Converting 2x2 to distribute volume.
        remove_brick_list = [self.brick_list[1], self.brick_list[4]]
        ret, _, _ = remove_brick(self.mnode, self.volname, remove_brick_list,
                                 'force', replica_count=1)
        self.assertEqual(ret, 0, "Failed to start remove brick operation")
        g.log.info("Remove brick operation successfully")

        # Checking if volume is pure distribute or not.
        volume_info = get_volume_info(self.mnode, self.volname)
        brick_count = int(volume_info[self.volname]['brickCount'])
        self.assertEqual(brick_count, 2, "Failed to remove 2 bricks.")
        g.log.info("Successfully removed 2 bricks.")
        type_string = volume_info[self.volname]['typeStr']
        self.assertEqual(type_string, 'Distribute',
                         "Convertion to distributed failed.")
        g.log.info("Convertion to distributed successful.")
