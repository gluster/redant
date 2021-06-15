"""
Copyright (C) 2019  Red Hat, Inc. <http://www.redhat.com>

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
    Test case to check enabling glusterd debug mode functionality.
"""

# disruptive;

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):

        # Stop glusterd
        self.redant.stop_glusterd(self.server_list[0])

        if not (self.redant.
                wait_for_glusterd_to_stop(self.server_list[0])):
            raise Exception(f"Glusterd still running on {self.server_list[0]}")

        # Reverting log level in /usr/lib/systemd/system/glusterd.service
        # to INFO
        glusterd_file = "/usr/local/lib/systemd/system/glusterd.service"
        ret = self.redant.find_and_replace_in_file(self.server_list[0],
                                                   'LOG_LEVEL=DEBUG',
                                                   'LOG_LEVEL=INFO',
                                                   glusterd_file)
        if not ret:
            raise Exception("Couldn't replace")

        # Archiving the glusterd log file of test case.
        deb_file = '/var/log/glusterfs/EnableDebugMode-glusterd.log'
        ret = self.redant.move_file(self.server_list[0],
                                    '/var/log/glusterfs/glusterd.log',
                                    deb_file)
        if not ret:
            raise Exception("Archiving present log file failed.")

        # Reverting back to old glusterd log file.
        ret = self.redant.move_file(self.server_list[0],
                                    '/var/log/glusterfs/old.log',
                                    '/var/log/glusterfs/glusterd.log')
        if not ret:
            raise Exception("Reverting glusterd log failed.")

        # Daemon should be reloaded as unit file is changed
        ret = self.redant.reload_glusterd_service(self.server_list[0])
        if not ret:
            raise Exception("Unable to reload the daemon")

        # Restart glusterd
        self.redant.start_glusterd(self.server_list[0])
        if not self.redant.wait_for_glusterd_to_start(self.server_list[0]):
            raise Exception(f"Glusterd not started on {self.server_list[0]}")

        super().terminate()

    def run_test(self, redant):
        """
        Testcase:
        1. Stop glusterd.
        2. Change log level to DEBUG in
           /usr/local/lib/systemd/system/glusterd.service.
        3. Remove glusterd log
        4. Start glusterd
        5. Issue some gluster commands
        6. Check for debug messages in glusterd log
        """
        # Stop glusterd
        redant.stop_glusterd(self.server_list[0])

        # Change log level in /usr/local/lib/systemd/system/glusterd.service
        # to DEBUG
        glusterd_file = "/usr/local/lib/systemd/system/glusterd.service"
        ret = redant.find_and_replace_in_file(self.server_list[0],
                                              'LOG_LEVEL=INFO',
                                              'LOG_LEVEL=DEBUG',
                                              glusterd_file)
        if not ret:
            raise Exception("Couldn't replace")

        # Archive old glusterd.log file.
        ret = redant.move_file(self.server_list[0],
                               '/var/log/glusterfs/glusterd.log',
                               '/var/log/glusterfs/old.log')

        if not ret:
            raise Exception("Renaming the glusterd log is failed")

        # Daemon reloading as the unit file of the daemon changed
        ret = redant.reload_glusterd_service(self.server_list[0])
        if not ret:
            raise Exception("Daemon reloaded successfully")

        # Start glusterd
        redant.start_glusterd(self.server_list[0])

        # Check if glusterd is running or not.
        if not redant.wait_for_glusterd_to_start(self.server_list[0]):
            raise Exception(f"Glusterd not running on {self.server_list[0]}\n")

        # Instead of executing commands in loop, if glusterd is restarted in
        # one of the nodes in the cluster the handshake messages
        # will be in debug mode.
        redant.restart_glusterd(self.server_list[1])

        if not redant.wait_for_glusterd_to_start(self.server_list[1]):
            raise Exception(f"Glusterd not running on {self.server_list[1]}")

        # Check glusterd logs for debug messages
        glusterd_log_file = "/var/log/glusterfs/glusterd.log"
        ret = redant.check_if_pattern_in_file(self.server_list[0], ' D ',
                                              glusterd_log_file)
        if ret != 0:
            raise Exception("Debug messages are not present in log.")
