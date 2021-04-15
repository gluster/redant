"""
This file contains a test-case which tests
volume related operations.
"""
#disruptive;dist

from tests.parent_test import ParentTest


class TestCase(ParentTest):
    """
    The test case contains one function to test
    volume creation and deletion.
    """

    def run_test(self, redant):
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
        redant.peer_probe(servera, serverb)
        redant.peer_probe(serverc, serverb)
        redant.peer_status(serverb)
        volname = "test-vol1"
        mountpoint = "/mnt/dist"
        redant.execute_io_cmd("ls -l /root", servera)
        redant.volume_create(volname,
                             [f"{servera}:/glusterfs/brick/brick1",
                              f"{serverb}:/glusterfs/brick/brick2",
                              f"{serverc}:/glusterfs/brick/brick3"],
                             serverb, force=True)
        redant.volume_start(volname, serverc)
        volume_status1 = redant.get_volume_status(serverb, volname)
        volume_status2 = redant.get_volume_status(serverc, volname)
        redant.execute_io_cmd(f"mkdir -p {mountpoint}", serverb)
        redant.volume_mount(servera, volname, mountpoint, serverb)
        redant.execute_io_cmd(f"cd {mountpoint} && touch " + "{1..100}",
                              serverb)
        redant.execute_io_cmd(f"ls -l {mountpoint}", serverb)
        redant.execute_io_cmd(f"cd {mountpoint} && rm -rf ./*", serverb)
        redant.execute_io_cmd(f"ls -l {mountpoint}", serverb)
        redant.volume_unmount(mountpoint, serverb)
        redant.volume_stop(volname, servera)
        redant.volume_delete(volname, servera)
        redant.execute_io_cmd(f"cd /mnt && rm -rf ./{volname}", serverb)
        redant.peer_detach(serverb, serverc)
        redant.peer_detach(serverb, servera)
