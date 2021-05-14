
"""
This file contains a test-case which tests glusterd
service operations
"""
# nonDisruptive;dist,rep,dist-rep,arb,dist-arb,disp,dist-disp

from tests.abstract_test import AbstractTest


class TestCase(AbstractTest):
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

        redant.execute_abstract_op_node("ls -l /root", servera)
        volume_status = redant.get_volume_status(self.vol_name, servera)
        redant.logger.info(volume_status)
        redant.execute_abstract_op_node(f"cd {self.mountpoint} "
                                        "&& touch " + "{1..100}",
                                        self.client_list[0])
        redant.execute_abstract_op_node(
            f"ls -l {self.mountpoint}", self.client_list[0])
        redant.execute_abstract_op_node(f"cd {self.mountpoint} && rm -rf ./*",
                                        self.client_list[0])
        redant.execute_abstract_op_node(
            f"ls -l {self.mountpoint}", self.client_list[0])

        try:
            redant.execute_abstract_op_node(
                "ls -l /non-exsisting-path", servera)
        except Exception as error:
            redant.logger.error(error)
