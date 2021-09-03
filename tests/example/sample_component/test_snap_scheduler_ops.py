"""
This file contains a test-case which tests
the SnapSchedulerOps ops.
"""

# disruptive;rep,dist,dist-rep,arb,dist-arb,disp,dist-disp
import traceback
from time import sleep
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):
    """
    SnapScheduler related testing.
    """
    def terminate(self):
        """
        Disable shared storage and snap_scheduler
        """
        try:
            if self.is_scheduler_enabled:
                # Disable snap scheduler
                self.redant.scheduler_disable(self.server_list[0], False)

                # Check snapshot scheduler status
                for server in self.server_list:
                    count = 0
                    while count < 40:
                        ret = self.redant.scheduler_status(server, False)
                        if ret['error_code'] != 0:
                            break
                        # status = status.strip().split(":")[2]
                        # if ret == 0 and status == ' Enabled':
                        #     break
                        sleep(2)
                        count += 1
                    if ret['error_code'] == 0:
                        raise Exception("Unexpected: Status of scheduler"
                                        f" on node {server} was successfull")

            # Check if shared storage is enabled
            # Disable if true
            ret = self.redant.is_shared_volume_mounted(self.server_list)
            if ret:
                ret = self.redant.disable_shared_storage(self.server_list[0])
                if not ret:
                    raise Exception("Failed to disable shared storage")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        In the testcase:
        Steps:
        1. Enable shared storage
        2. Check if the shared storage is enabled
        3. Initalize snap_scheduler
        4. Enable snap_scheduler
        5. Check snap_scheduler status
        6. Disable snap_scheduler
        """
        self.is_scheduler_enabled = False

        # Enable shared storage
        ret = redant.enable_shared_storage(self.server_list[0])
        if not ret:
            raise Exception("Failed to enable shared storage")

        # Validate shared storage volume is mounted
        ret = redant.is_shared_volume_mounted(self.server_list[0], timeout=10)
        if not ret:
            raise Exception("Failed to validate if shared volume is mounted")

        # Initialise snap_scheduler on all nodes
        count = 0
        sleep(2)
        while count < 40:
            ret = redant.scheduler_init(self.server_list)
            if ret:
                break
            sleep(2)
            count += 1
        if not ret:
            raise Exception("Failed to initialize scheduler on all nodes")

        # Enable snap_scheduler
        redant.scheduler_enable(self.server_list[0])
        self.is_scheduler_enabled = True

        # Check snapshot scheduler status
        for server in self.server_list:
            count = 0
            while count < 40:
                ret = redant.scheduler_status(server, False)
                if ret['error_code'] == 0:
                    break
                # status = status.strip().split(":")[2]
                # if ret == 0 and status == ' Enabled':
                #     break
                sleep(2)
                count += 1
            if ret['error_code'] != 0:
                raise Exception("Failed to check status of scheduler"
                                f" on node {server}")

        # Disable snap scheduler
        redant.scheduler_disable(self.server_list[0], False)
        self.is_scheduler_enabled = False

        # Check snapshot scheduler status
        for server in self.server_list:
            count = 0
            while count < 40:
                ret = redant.scheduler_status(server, False)
                if ret['error_code'] != 0:
                    break
                # status = status.strip().split(":")[2]
                # if ret == 0 and status == ' Enabled':
                #     break
                sleep(2)
                count += 1
            if ret['error_code'] == 0:
                raise Exception("Unexpected: Status of scheduler"
                                f" on node {server} was successfull")
