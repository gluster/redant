# Shared Storage Ops

[Shared Storage Ops](../../../common/ops/gluster_ops/shared_storage_ops.py) contains all the functions which are required for the shared storage operations.

1) **enable_shared_storage**<br>

        This function enables the shared storage option.

        Args:
            node (str) : Node on which command is to be executed

        Returns:
            bool : True if successfully enabled shared storage.
                   False otherwise.

        Example:
            ret = self.redant.enable_shared_storage(self.server_list[0])



2) **disable_shared_storage**<br>

        This function disables the shared storage option.

        Args:
            node (str) : Node on which command is to be executed

        Returns:
            bool : True if successfully disabled shared storage.
                   False otherwise.
            
        Example:
            ret = self.redant.disable_shared_storage(self.server_list[0])



3) **is_shared_volume_mounted_or_unmounted**<br>

        This function checks if shared storage volume is mounted or not.

        Args:
            1. node (str) : Node on which command is to be executed
        Optional:
            2. timeout(int) : Maximum time allowed to check for shared volume

        Returns:
            bool : True if shared storage volume is mounted/unmounted as
                   expected, False otherwise.

        Example:
            ret = self.redant.is_shared_volume_mounted_or_unmounted(node,
                                                                    mounted)



4) **check_gluster_shared_volume**<br>

        This function checks if gluster shared volume is present or absent.

        Args:
            1. node (str) : Node on which command is to be executed
        Optional:
            2. present (bool) : True if you want to check presence
                                False if you want to check absence.
            3. timeout(int) : Maximum time allowed to check for shared volume

        Returns:
            bool : True if gluster_shared_storage volume present/absent in
                   volume list as expected, False otherwise.

        Example:
            ret = self.redant.check_gluster_shared_volume(self.server_list[0])
