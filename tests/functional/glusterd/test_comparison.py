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
        servera = self.server_list[0]
        serverb = self.server_list[1]
        serverc = self.server_list[2]
        try:
            self.redant.peer_probe(servera, serverb)
            self.redant.peer_probe(serverc, serverb)
            volname = "test-vol1"
            mountpoint = "/mnt/dist"
            self.redant.run(servera,"ls -l /root")
            self.redant.volume_create(volname,
                                      [f"{servera}:/glusterfs/brick/brick1",
                                      f"{serverb}:/glusterfs/brick/brick2",
                                      f"{serverc}:/glusterfs/brick/brick3"],
                                      servera, force=True)
            self.redant.volume_start(volname,servera)
            volume_status1 = self.redant.get_volume_status(serverb,volname)
            volume_status2 = self.redant.get_volume_status(serverc,volname)
            self.redant.run(serverb, f"mkdir -p {mountpoint}")
            self.redant.volume_mount(servera,volname,mountpoint,serverb)
            self.redant.run(serverb, f"cd {mountpoint} && touch " + "{1..100}")
            self.redant.run(serverb, f"ls -l {mountpoint}")
            self.redant.run(serverb, f"cd {mountpoint} && rm -rf ./*")
            self.redant.run(serverb, f"ls -l {mountpoint}")
            self.redant.volume_stop(volname,servera)
            self.redant.volume_delete(volname,servera)
            self.redant.volume_unmount(mountpoint,serverb)
            self.redant.run(serverb, f"cd /mnt && rm -rf ./{volname}")
            self.redant.peer_detach(serverb, serverc)
            self.redant.peer_detach(serverb, servera)
            
        except Exception as error:
            self.TEST_RES = False
            print(f"Test Failed:{error}")
