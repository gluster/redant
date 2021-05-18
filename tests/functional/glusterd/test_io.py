"""
This file contains a test-case which tests glusterd
starting and stopping of glusterd service.
"""
# nonDisruptive;dist

from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):
    """
    The test case contains one function to test
    for glusterd service operations
    """

    def run_test(self, redant):
        """
        This particular test case tests the io_functions
        on mountpoints. The steps taken are:
        1) call collect_mounts_arequal function
        2) call get_mounts_stat function
        3) call list_all_files_and_dirs_mounts function
        4) execute a command in async and call validate_io_procs function
        5) call cleanup_mounts
        """

        # redant.collect_mounts_arequal(mountpoints)
        redant.get_mounts_stat(self.mountpoint)
        redant.list_all_files_and_dirs_mounts(self.mountpoint)
        async_obj = redant.execute_command_async("ls", self.server_list[0])
        redant.validate_io_procs(async_obj, self.mountpoint)
        redant.cleanup_mounts(self.mountpoint)
