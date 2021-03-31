"""
This file contains a test-case which tests
directory creation and deletion,file creation
and listing the contents.
"""
# disruptive;dist,rep,arb,disp

from tests.parent_test import ParentTest


class TestCase(ParentTest):
    """
    The test case contains one function to test
    for directory creation ,file creation, list its
    contents and deletion of directory.
    """

    def run_test(self):
        """
        In the testcase:
        1) glusterd service is started on the server.
        2) Directory is created
        3) File is created
        4) List the contents
        5) Delete the directory
        6) glusterd service is stopped.
        """
        server = self.server_list[0]
        try:
            self.redant.glusterd_start(server)

            dir_path = '/test_dir'
            file_path = '/test_dir/file1.txt'

            self.redant.mkdir(server, dir_path)

            self.redant.touch(server, file_path)

            self.redant.ls(server, dir_path)

            self.rmdir(server, dir_path, True)

            self.redant.glusterd_stop(server)
            print("Test Passed")

        except Exception as error:
            self.TEST_RES = False
            print(f"Test Failed:{error}")
