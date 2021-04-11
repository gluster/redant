"""
This file contains a test-case which tests
the creation of different types of files and
some operations on it.
"""
#disruptive;

from tests.parent_test import ParentTest


class TestCase(ParentTest):
    """
    The test case contains one function to test
    for the creation of different types of files and
    some operations on it.
    """

    def run_test(self):
        """
        In the testcase:
        1) A mount-point is created
        2) A regular file is created.
        3) Block , char and pipefile is created.
        4) Append some data to file.
        5) Check if data has been appended.
        6) Look-up on mount-point.
        7) Mount-point is deleted.
        """
        host = self.server_list[0]
        regfile_name = "file1"
        mountpoint = "/mnt/test_dir"
        self.redant.execute_io_cmd(f"mkdir -p {mountpoint}", host)
        self.redant.execute_io_cmd(
            f"cd {mountpoint} && touch {mountpoint}/{regfile_name}", host)

        for (file_name, parameter) in [
                ("blockfile", "b"), ("charfile", "c")]:
                self.redant.execute_io_cmd(
                f"mknod {mountpoint}/{file_name} {parameter} 1 5", host)

        self.redant.execute_io_cmd(f"mkfifo {mountpoint}/pipefile", host)

        for (file_name, data_str) in [
            ("regfile", "regular"),
            ("charfile", "character special"),
            ("blockfile", "block special")]:
            str_to_add = f"This is a {data_str} file."
            path = f"{mountpoint}/{regfile_name}"
            self.redant.execute_io_cmd(
                f"echo '{str_to_add}' >> {path}", host)

        self.redant.execute_io_cmd(f"cat {path}", host)
        self.redant.execute_io_cmd(f"ls -lR {mountpoint}", host)
        self.redant.execute_io_cmd(f"rm -rf {mountpoint}", host)
