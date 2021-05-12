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
        1) create 2 directories for mountpoints
        2) create 2 files - one in each mountpoint
        3) mount the mountpoints to the volume
        4) extract the mountpoints as dict from volds
        5) call collect_mounts_arequal function
        6) call get_mounts_stat function
        7) call list_all_files_and_dirs_mounts function
        8) execute a command in async and call validate_io_procs function
        9) unmount the mountpoints
        10) call cleanup_mounts
        11) Delete the mountpoint directories.
        """

        volumes = self.redant.volds.keys()
        volumes = list(volumes)
        redant.create_dirs(self.server_list[0], [
                           "/root/mount1", "/root/mount2"])
        redant.create_file("/root/mount1", "file1.txt", self.server_list[0])
        redant.create_file("/root/mount2", "file2.txt", self.server_list[0])
        redant.volume_mount(self.server_list[0], volumes[0],
                            "/root/mount1", self.server_list[0])
        redant.volume_mount(self.server_list[0], volumes[0],
                            "/root/mount2", self.server_list[0])

        mountpoints = []
        for vol in volumes:
            mountpoints += redant.get_mnt_pts_dict_in_list(vol)

        # redant.collect_mounts_arequal(mountpoints)
        redant.get_mounts_stat(mountpoints)
        redant.list_all_files_and_dirs_mounts(mountpoints)
        async_obj = redant.execute_command_async("ls", self.server_list[0])
        redant.validate_io_procs(async_obj, mountpoints)
        redant.volume_unmount(volumes[0], "/root/mount1", self.server_list[0])
        redant.volume_unmount(volumes[0], "/root/mount2", self.server_list[0])
        redant.cleanup_mounts(mountpoints)
        redant.execute_abstract_op_node(
            "rm -rf /root/mount1", self.server_list[0])
        redant.execute_abstract_op_node(
            "rm -rf /root/mount2", self.server_list[0])
