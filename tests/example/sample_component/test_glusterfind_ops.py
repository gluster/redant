"""
This file contains a test-case which tests
the creation of different volume types.
"""
# disruptive;rep,dist,dist-rep,disp,dist-disp

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):
    """
    The test case contains one function to test
    for the creation of different types of files and
    some operations on it.
    """

    def run_test(self, redant):
        """
        In the testcase:
        """
        # Create a session
        sess1 = "validsession"
        redant.gfind_create(self.server_list[0], self.vol_name, sess1)

        # List session
        redant.gfind_list(self.server_list[0], self.vol_name, sess1)

        # Perfrom a glusterfind pre for the session
        outfiles = [f"/tmp/test-outfile-{self.vol_name}-{i}.txt"
                    for i in range(0, 2)]
        redant.gfind_pre(self.server_list[0], self.vol_name, sess1,
                         outfiles[0], full=True, noencode=True, debug=True)

        if not redant.path_exists(self.server_list[0], outfiles[0]):
            raise Exception("File doesn't exists")

        # Perform glusterfind post for the session
        redant.gfind_post(self.server_list[0], self.vol_name, sess1)

        # Perform glusterfind query
        redant.gfind_query(self.server_list[0], self.vol_name, outfiles[0],
                           full=True)

        # Perform glusterfind delete
        redant.gfind_delete(self.server_list[0], self.vol_name, sess1)
