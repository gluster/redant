# Heal Ops

[Heal Ops](../../../common/ops/gluster_ops/heal_ops.py) contains all the functions which are required for heal operations.

1) **wait_for_self_heal_daemons_to_be_online**<br>
        This function waits for the volume self-heal-daemons to be online until timeout.

        Args:
            volname (str): Name of the volume.
            node (str): Node on which commands will be executed.

        Optional:
            timeout (int): timeout value in seconds to wait for
                           self-heal-daemons to be online.

        Returns:
            bool : True if all self-heal-daemons are online within timeout,
                   False otherwise

        Example:
            self_heal_daemon_online_status = (
            self.wait_for_self_heal_daemons_to_be_online(volname, node,
                                                         timeout))

2) **are_all_self_heal_daemons_online**<br>
        This function verifies whether all the self-heal-daemons are online for the
        specified volume.

        Args:
            volname (str): volume name
            node (str): Node on which cmd has to be executed.

        Returns:
            bool : True if all the self-heal-daemons are online for the volume.
                   False otherwise.
            NoneType: None if unable to get the volume status

        Example:
            status = self.are_all_self_heal_daemons_online(volname, node)

        