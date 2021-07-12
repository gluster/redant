"""
Copyright (C) 2015-2019  Red Hat, Inc. <http://www.redhat.com>

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
# nonDisruptive;rep
from tests.nd_parent_test import NdParentTest

class TestCase(NdParentTest):

    # @classmethod
    # def create_user(cls, host, user):
    #     """
    #     Creates a user on a host
    #     """
    #     g.log.info("Creating user '%s' for %s...", user, host)
    #     command = "useradd %s" % user
    #     _, _, err = g.run(host, command)

    #     if 'already exists' in err:
    #         g.log.warn("User '%s' is already exists on %s", user, host)
    #     else:
    #         g.log.info("User '%s' is created successfully on %s", user, host)

    # @classmethod
    # def delete_user(cls, host, user):
    #     """
    #     Deletes a user on a host
    #     """
    #     g.log.info('Deleting user %s from %s...', user, host)
    #     command = "userdel -r %s" % user
    #     _, _, err = g.run(host, command)

    #     if 'does not exist' in err:
    #         g.log.warn('User %s is already deleted on %s', user, host)
    #     else:
    #         g.log.info('User %s successfully deleted on %s', user, host)

    # def setUp(self):
    #     self.get_super_method(self, 'setUp')()

    #     # Create user qa
    #     for mount_object in self.mounts:
    #         self.create_user(mount_object.client_system, 'qa')

    #     for server in self.servers:
    #         self.create_user(server, 'qa')

    #     # Setup Volume and Mount Volume
    #     g.log.info("Starting to Setup Volume and Mount Volume")
    #     ret = self.setup_volume_and_mount_volume(mounts=self.mounts)
    #     if not ret:
    #         raise ExecutionError("Failed to Setup_Volume and Mount_Volume")
    #     g.log.info("Successful in Setup Volume and Mount Volume")

    #     self.bricks_list = get_all_bricks(self.mnode, self.volname)
    #     self.assertIsNotNone(self.bricks_list, "unable to get list of bricks")

    # def terminate(self):
    #     """
    #     Cleanup and umount volume
    #     """

    #     # Delete user
    #     for mount_object in self.mounts:
    #         self.delete_user(mount_object.client_system, 'qa')

    #     for server in self.servers:
    #         self.delete_user(server, 'qa')


    def run_test(self, redant):
        """
        Description:
        - create file file.txt on mountpoint
        - change uid, gid and permission from client
        - check uid, gid and permission on client and all servers
        """
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        # Create user qa
        if not redant.add_user(self.mnt_list, 'qa'):
            raise Exception(f"Failed to add user in {self.mnt_list}")

        if not redant.add_user(self.server_list, 'qa'):
            raise Exception(f"Failed to add user in {self.server_list}")
        self.bricks_list = redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])
        if self.bricks_list is None:
            raise Exception("Failed to get the list of bricks")
        # create file
        # cmd = ("dd if=/dev/urandom of=%s/file.txt bs=1M count=1"
        #        % self.mounts[0].mountpoint)
        # ret, _, _ = g.run(self.clients[0], cmd)
        # self.assertEqual(ret, 0, "File creation failed")

        # # Adding servers and client in single dict to check permissions
        # nodes_to_check = {}
        # all_bricks = get_all_bricks(self.mnode, self.volname)
        # for brick in all_bricks:
        #     node, brick_path = brick.split(':')
        #     nodes_to_check[node] = brick_path
        # nodes_to_check[self.mounts[0].client_system] = \
        #     self.mounts[0].mountpoint

        # # check file is created on all bricks and client
        # for node in nodes_to_check:
        #     filepath = nodes_to_check[node] + "/file.txt"
        #     stat_dict = get_file_stat(node, filepath)
        #     self.assertIsNotNone(stat_dict, "stat on %s failed" % filepath)
        #     self.assertEqual(stat_dict['filetype'], 'regular file',
        #                      "Expected regular file but found %s"
        #                      % stat_dict['filetype'])

        # # get file stat info from client
        # fpath = self.mounts[0].mountpoint + "/file.txt"
        # stat_dict = get_file_stat(self.clients[0], fpath)
        # self.assertIsNotNone(stat_dict, "stat on %s failed" % fpath)
        # self.assertEqual(stat_dict['uid'], '0', "Expected uid 0 but found %s"
        #                  % stat_dict['uid'])
        # self.assertEqual(stat_dict['gid'], '0', "Expected gid 0 but found %s"
        #                  % stat_dict['gid'])
        # self.assertEqual(stat_dict['access'], '644', "Expected permission 644"
        #                  " but found %s" % stat_dict['access'])

        # # change uid, gid and permission from client
        # cmd = ("chown qa %s" % fpath)
        # ret, _, _ = g.run(self.clients[0], cmd)
        # self.assertEqual(ret, 0, "chown failed")

        # cmd = ("chgrp qa %s" % fpath)
        # ret, _, _ = g.run(self.clients[0], cmd)
        # self.assertEqual(ret, 0, "chgrp failed")

        # cmd = ("chmod 777 %s" % fpath)
        # ret, _, _ = g.run(self.clients[0], cmd)
        # self.assertEqual(ret, 0, "chown failed")

        # # Verify that the changes are successful on bricks and client
        # for node in nodes_to_check:
        #     filepath = nodes_to_check[node] + "/file.txt"
        #     stat_dict = get_file_stat(node, filepath)
        #     self.assertIsNotNone(stat_dict, "stat on %s failed" % fpath)
        #     self.assertEqual(stat_dict['username'], 'qa',
        #                      "Expected qa but found %s"
        #                      % stat_dict['username'])
        #     self.assertEqual(stat_dict['groupname'], 'qa',
        #                      "Expected gid qa but found %s"
        #                      % stat_dict['groupname'])
        #     self.assertEqual(stat_dict['access'], '777',
        #                      "Expected permission 777  but found %s"
        #                      % stat_dict['access'])
