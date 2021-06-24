"""
This test case deals with checking the functionalities
related to user and groups
"""

# disruptive;rep

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        if not redant.add_user(self.server_list, "test-user"):
            raise Exception("Couldn't add the user")
        if not redant.add_user(self.server_list, "test-user"):
            raise Exception("Couldn't add the user")

        if not redant.del_user(self.server_list, "test-user"):
            raise Exception("Couldn't delete the user")

        if not redant.del_user(self.server_list[2], "test-user"):
            raise Exception("Couldn't delete the user")

        # group related functions
        if not redant.group_add(self.server_list, "test-group"):
            raise Exception("Failed to add group")
        if not redant.group_add(self.server_list, "test-group"):
            raise Exception("Failed to add group")
        if not redant.group_del(self.server_list, "test-group"):
            raise Exception("Failed to delete the group")
        if not redant.group_del(self.server_list, "test-group"):
            raise Exception("Failed to delete the group")