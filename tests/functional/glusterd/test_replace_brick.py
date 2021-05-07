"""
This file contains a test case
that checks the replace-brick functionality
"""
#disruptive;dist-rep
from tests.parent_test import ParentTest

class TestReplaceBrick(ParentTest):
    """
    This test class tests the add-brick
    functionality 
    """

    def run_test(self):
        """
        The following steps are undertaken in the testcase:
        1) Peer probed to all the servers
        2) Volume is set up
        3) Bricks are replaced
        4) Bricks are deleted
        5) Volume is deleted
        6) Peers are detached
        """
  
        pass
        # try:
        #     self.redant.replace_brick(servera, volname, f"{serverb}:/data/glusterfs/avol/brick2", f"{serverc}:/data/glusterfs/avol/brick3")
        # except Exception as error:
        #     self.TEST_RES = False
        #     print(f"Test failed:{error}")