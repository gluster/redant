"""
This file contains a test-case which tests glusterd
starting and stopping of glusterd service.
"""
#disruptive;dist

from tests.parent_test import ParentTest


class TestCase(ParentTest):
    """
    The test case contains one function to test
    for glusterd service operations
    """

    def run_test(self):
        """
        The following steps are undertaken in the testcase:
        1) glusterd service is started on the server
        2) Volumes are created
        3) Volumes are started
        4) Volume list is fetched
        5) volume options are set on all volumes
        6) Volumes are stopped
        7) glusterd service is stopped
        """
        server = self.server_list[0]
        try:
            volname = "test-vol1"
            mountpoint = "/mnt/dist"
            self.redant.run(server,"ls -l /root")
            self.redant.volume_create(volname,
                                      [f"{server}:/root/bricks/brick1",
                                      f"{server}:/root/bricks/brick2",
                                      f"{server}:/root/bricks/brick3"],server,
                                      force=True)
            self.redant.volume_start(volname,server)
            volume_status1 = self.redant.get_volume_status(server,volname)
            volume_status2 = self.redant.get_volume_status(server,volname)
            self.redant.run(server, "cd /mnt; mkdir " + volname)
            self.redant.run(server, "cd /mnt; mkdir " + mountpoint)
            self.redant.volume_mount(server,volname,mountpoint,server)
            self.redant.run(server, "cd " + mountpoint + "; touch {1..100}")
            self.redant.run(server, "ls -l " + mountpoint)
            self.redant.run(server, "cd " + mountpoint + "; rm -rf *")
            self.redant.run(server, "ls -l " + mountpoint)
            self.redant.volume_stop(volname,server)
            self.redant.volume_delete(volname,server)
            self.redant.volume_unmount(mountpoint,server)
            self.redant.run(server, "cd /mnt; rm -rf " + volname)
            self.redant.run(server, "rm -rf " + mountpoint)
            
        except Exception as error:
            self.TEST_RES = False
            print(f"Test Failed:{error}")
