"""
This file contains a test-case which tests glusterd
starting and stopping of glusterd service.
"""
#disruptive;dist,rep,arb,disp,dist-rep,dist-arb

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
            self.redant.volume_create("test-vol1",[f"{server}:/brick1",
                                      f"{server}:/brick3"],server,
                                      force=True)
            self.redant.volume_create("test-vol2",
                                      [f"{server}:/brick2"], server,
                                      force=True)
            self.redant.volume_start("test-vol1",server)
            self.redant.volume_start("test-vol2",server)
            volume_list = self.redant.get_volume_list(server)
            options = {"user.cifs":"enable","user.smb":"enable"}
            for volume in volume_list:
                self.redant.set_volume_options(volume, options,server)
            self.redant.volume_stop("test-vol1",server)
            self.redant.volume_stop("test-vol2",server)
            self.redant.volume_delete("test-vol1",server)
            self.redant.volume_delete("test-vol2", server)
        except Exception as error:
            self.TEST_RES = False
            print(f"Test Failed:{error}")
