# Proifle Ops:

The code can be found at [profile_ops.py](../../../common/ops/gluster_ops/profile_ops.py)

1) **profile_start**<br>

        This function starts profile on the specified volume.

        Args:
            1. volname (str): Volume on which profile has to be started.
            2. node (str): Node on which command has to be executed.
            3. excep (bool): exception flag to bypass the exception if the
                             profile start command fails. If set to False
                             the exception is bypassed and value from remote
                             executioner is returned. Defaults to True
        Returns:
            ret: A dictionary consisting
                    - Flag : Flag to check if connection failed
                    - msg : message
                    - error_msg: error message
                    - error_code: error code returned
                    - cmd : command that got executed
                    - node : node on which the command got executed

        Example:
            redant.profile_start(self.server_list[0], self.vol_name)

2) **profile_info**<br>

        This function runs profile info on the specified volume.

        Args:
            1. volname (str): Volume for which profile info has to be retrived.
            2. node (str): Node on which command has to be executed.
            3. options (str): Options can be
                              [peek|incremental [peek]|cumulative|clear].If not
                              given the function returns the output of gluster
                              volume profile <volname> info.
            4. excep (bool): exception flag to bypass the exception if the
                             profile info command fails. If set to False
                             the exception is bypassed and value from remote
                             executioner is returned. Defaults to True
        Returns:
            ret: A dictionary consisting
                    - Flag : Flag to check if connection failed
                    - msg : message
                    - error_msg: error message
                    - error_code: error code returned
                    - cmd : command that got executed
                    - node : node on which the command got executed
            None: If invalid option is given.

        Example:
            redant.profile_info(self.server_list[0], self.vol_name)

3) **profile_stop**<br>

        This function stop profile on the specified volume.

        Args:
            1. volname (str): Volume on which profile has to be stopped.
            2. node (str): Node on which command has to be executed.
            3. excep (bool): exception flag to bypass the exception if the
                             profile stop command fails. If set to False
                             the exception is bypassed and value from remote
                             executioner is returned. Defaults to True
        Returns:
            ret: A dictionary consisting
                    - Flag : Flag to check if connection failed
                    - msg : message
                    - error_msg: error message
                    - error_code: error code returned
                    - cmd : command that got executed
                    - node : node on which the command got executed
        Example:
            redant.profile_stop(self.server_list[0], self.vol_name)

4) **check_profile_options**<br>

        This function helps in validating the profile options.

        Args:
            options (str): Options can be nothing or
                           [peek|incremental [peek]|cumulative|clear].
        Returns:
            True: If valid option is given.
            False: If invalid option is given

        Example:
            ret = redant.check_profile_options('peek')