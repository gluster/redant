
"""
This file contains a test-case which tests glusterd
service operations
"""
# nonDisruptive;dist,rep,dist-rep,arb,dist-arb,disp,dist-disp

from tests.parent_test import ParentTest


class TestCase(ParentTest):
    """
    The test case contains one function to test
    for glusterd service operations
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

        redant.execute_io_cmd("ls -l /root", servera)
        volume_status = redant.get_volume_status(self.vol_name, servera)
        redant.logger.info(volume_status)
        redant.execute_io_cmd(f"cd {self.mountpoint} && touch " + "{1..100}",
                              self.client_list[0])
        redant.execute_io_cmd(f"ls -l {self.mountpoint}", self.client_list[0])
        redant.execute_io_cmd(f"cd {self.mountpoint} && rm -rf ./*",
                              self.client_list[0])
        redant.execute_io_cmd(f"ls -l {self.mountpoint}", self.client_list[0])

        try:
            redant.execute_io_cmd("ls -l /non-exsisting-path", servera)
        except Exception as error:
            redant.logger.error(error)
            pass
