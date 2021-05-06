"""
This file contains a test case
that checks the add-brick functionality
"""
#disruptive;dist-rep
from tests.parent_test import ParentTest

class TestAddBrick(ParentTest):
    """
    This test class tests the add-brick
    functionality 
    """

    def run_test(self):
        """
        The following steps are undertaken in the testcase:
        1) Peer probed to all the servers
        2) Volume is set up
        3) Bricks are added
        4) Bricks are deleted
        5) Volume is deleted
        6) Peers are detached
        """
        servera = self.server_list[0]
        serverb = self.server_list[1]
        serverc = self.server_list[2]

        try:
            volname = "test-vol1"
            mountpoint = "/mnt/dist"
            self.redant.peer_probe(servera, serverb)
            self.redant.peer_status(serverb)
            self.redant.volume_create(volname,
                                      [f"{servera}:/data/glusterfs/avol/brick1",
                                       f"{serverb}:/data/glusterfs/avol/brick2"],
                                      servera, force=True)
            self.redant.volume_start(volname, serverb)
            volume_status1 = self.redant.get_volume_status(servera, volname)
            volume_status2 = self.redant.get_volume_status(serverb, volname)
            self.redant.execute_io_cmd(f"mkdir -p {mountpoint}", serverb)
            self.redant.volume_mount(servera, volname, mountpoint, serverb)
            self.redant.peer_probe(serverc, serverb)
            self.redant.add_brick(servera, volname, [f"{serverc}:/data/glusterfs/avol/brick3"], True)
            # self.redant.remove_brick(servera, volname, [f"{serverc}:/data/glusterfs/avol/brick3"], 'force')
            self.redant.volume_stop(volname, servera)
            self.redant.volume_delete(volname, servera)
            self.redant.volume_unmount(mountpoint, serverb)
            self.redant.execute_io_cmd(
                f"cd /mnt && rm -rf ./{volname}", serverb)
            self.redant.peer_detach(serverb, serverc)
            self.redant.peer_detach(serverb, servera)
        except Exception as error:
            self.TEST_RES = False
            print(f"Test failed:{error}")