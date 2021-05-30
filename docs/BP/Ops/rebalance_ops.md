# Rebalance Ops

[Rebalance Ops](../../../common/ops/gluster_ops/rebalance_ops.py) contains all the functions which are required for rebalance operations.

## Given below are all the details about all the functions implemented in the Rebalance Ops module:

1) **rebalance_start**<br>
        To start rebalance on a given node for a given volume

        Args:
            1. volname (str): Name of the volume
            2. node (str): Node in which rebalance is to be run.
            3. fix_layout (bool): Optional parameter with default value of False. If set rebalance will happen with fix-layout.
            4. force (bool): Optional parameter with default value of False. If set rebalance will be executed by force option.
            5. excep (bool): Optional parameter with default value of True. If set, exception handling is done at the abstract ops layer.
        Returns:
            A dictionary consisting
                1. Flag : Flag to check if connection failed
                2. msg : message
                3. error_msg: error message
                4. error_code: error code returned
                5. cmd : command that got executed
                6. node : node on which the command got executed
        Example:
            redant.rebalance_start(self.vol_name, self.server_list[0], excep=False)

2) **get_rebalance_status**<br>
        Function to get the rebalance status for a given volume.

        Args:
            1. volname (str): Name of the volume whose rebalance status is to be checked.
            2. node (str): Nodes wherein the rebalance status is to be checked.
        Returns:
            A dictionary showing the rebalance status.
        Example:
            ret = redant.get_rebalance_status(self.vol_name, self.server_list)

3) **wait_for_fix_layout_to_complete**<br>
        Function to wait for the fix layout to complete.

        Args:
            1. node (str): The node for in which we check the fix-layout.
            2. volname (str): Name of the volume whose fix-layout is to be checked.
            3. timeout (int): Default value 300. We will wait for x seconds till the fix-layout is finished.
        Returns:
            Boolean value. True if the node comes up within timeout or else False.
	Example:
            ret = self.wait_for_fix_layout_to_complete(self.server_list[0], self.vol_name)

4) **wait_for_rebalance_to_complete**<br>
        Function to wait for the rebalance to complete.

        Args:
            1. volname (str): Name of the volume whose rebalance status is to be checked.
            2. node (str): The node for in which we check the rebalance status.
            3. timeout (int): Default value 300. We will wait for x seconds till the rebalance is finished.
        Returns:
            Boolean value. True if the node comes up within timeout or else False.
	Example:
            ret = self.wait_for_fix_layout_to_complete(self.server_list[0], self.vol_name)
