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
        1) Volume is created
        2) Volume is started
        3) Volume status is fetched
        4) Mountpoint is mounted to volume
        5) Io operations are performed
        6) Volume is Stopped
        7) Volume is Deleted
        8) Mountpoint is unmounted
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
