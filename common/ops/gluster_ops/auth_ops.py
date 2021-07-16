"""
Auth ops module deals with the auth allow and reject operations
"""

from common.ops.abstract_ops import AbstractOps


class AuthOps(AbstractOps):
    """
    Class which is responsible for methods for auth allow and
    reject operations.
    """
    def set_auth_allow(self, volname: str, server: str,
                       auth_dict: dict) -> bool:
        """
        Set authentication for volumes or sub directories as required

        Args:
            volname(str): The name of volume in which auth.allow
                has to be set
            server(str): IP or hostname of one node
            auth_dict(dict): key-value pair of dirs and clients list
                Example: auth_dict = {'/d1':['10.70.37.172','10.70.37,173'],
                    '/d3/subd1':['10.70.37.172',
                        'dhcp37-999.xyz.cdf.pqr.abc.com']}
                If authentication has to set on entire volume,
                use 'all' as key.
                    auth_dict = {'all': ['10.70.37.172','10.70.37,173']}
                    auth_dict = {'all': ['*']}
                    'all' refers to entire volume
        Returns (bool):
            True if all the auth.allow set operation is success, else False
        """
        auth_cmds = []
        if not auth_dict:
            self.logger.error("Authentication details are not provided.")
            return False

        # If authentication has to be set on sub-dirs, convert
        # the key-value pair
        # to gluster authentication set command format.
        if 'all' not in auth_dict:
            for key, value in list(auth_dict.items()):
                auth_cmds.append(f"{key}({'|'.join(value)})")
            auth_cmd = (f"gluster volume set {volname}"
                        f" auth.allow \"{','.join(auth_cmds)}\"")

        # When authentication has to be set on entire volume, convert the
        # key-value pair to gluster authentication set command format
        else:
            auth_cmd = (f"gluster volume set {volname}"
                        f" auth.allow \"{','.join(auth_dict['all'])}\"")

        # Execute auth.allow setting on server
        ret = self.execute_abstract_op_node(auth_cmd, server, False)
        if ret['error_code'] == 0 and self.verify_auth_allow(volname,
                                                             server,
                                                             auth_dict):
            self.logger.info("Authentication set and verified successfully.")
            return True

        return False

    def verify_auth_allow(self, volname: str, server: str,
                          auth_dict: dict) -> bool:
        """
        Verify authentication for volumes or sub directories as required

        Args:
            volname(str): The name of volume in which auth.allow
                has to be verified
            server(str): IP or hostname of one node
            auth_dict(dict): key-value pair of dirs and clients list
                Example: auth_dict = {'/d1':['10.70.37.172',
                '10.70.37,173'],
                    '/d3/subd1':['10.70.37.172','10.70.37.197']}
                If authentication is set on entire volume,
                use 'all' as key to
                verify.
                    auth_dict = {'all': ['10.70.37.172',
                    '10.70.37,173']}
                    auth_dict = {'all': ['*']}
                    'all' refers to entire volume
        Returns (bool):
            True if the verification is success, else False
        """
        auth_details = []
        if not auth_dict:
            self.logger.error("Authentication details are not "
                              "provided.")
            return False

        # Get the value of auth.allow option of the volume
        auth_clients_dict = self.get_volume_options(volname,
                                                    "auth.allow",
                                                    server)
        auth_clients = auth_clients_dict['auth.allow']

        # When authentication has to be verified on entire
        # volume(not on sub-dirs) check whether the required
        # clients names are listed in auth.allow option
        if 'all' in auth_dict:
            clients_list = auth_clients.split(",")
            res = all(elem in clients_list for elem in auth_dict['all'])
            if not res:
                self.logger.error("Authentication verification failed."
                                  f" auth.allow: {auth_clients}")
                return False
            self.logger.info("Authentication verified successfully. "
                             f"auth.allow: {auth_clients}")
            return True

        # When authentication has to be verified on sub-dirs, convert the
        # key-value pair to a format which matches
        # the value of auth.allow option
        for key, value in list(auth_dict.items()):
            auth_details.append(f"{key}({'|'.join(value)})")

        # Check whether the required clients names are listed
        # in auth.allow option
        for auth_detail in auth_details:
            if auth_detail not in auth_clients:
                self.logger.error("Authentication verification failed."
                                  f" auth.allow: {auth_clients}")
                return False
        self.logger.info("Authentication verified successfully."
                         f" auth.allow: {auth_clients}")
        return True

    def verify_auth_reject(self, volname: str, server: str,
                           auth_dict: dict) -> bool:
        """
        Verify auth reject for volumes or sub directories as required

        Args:
            volname(str): The name of volume in which auth.reject
                          has to be verified.
            server(str): IP or hostname of one node
            auth_dict(dict): key-value pair of dirs and clients list
                Example: auth_dict = {'/d1':['10.70.37.172','
                                            10.70.37,173'],
                    '/d3/subd1':['10.70.37.172',
                                 'dhcp37-999.xyz.cdf.pqr.abc.com']}
                If authentication is set on entire volume,
                use 'all' as key to
                verify.
                    auth_dict = {'all': ['10.70.37.172',
                                         '10.70.37,173']}
                    auth_dict = {'all': ['*']}
                    'all' refer to entire volume
        Returns (bool):
            True if all the verification is success, else False
        """
        auth_details = []
        if not auth_dict:
            self.logger.error("Authentication details are not provided")
            return False

        # Get the value of auth.reject option of the volume
        auth_clients_dict = self.get_volume_options(volname,
                                                    "auth.reject",
                                                    server)
        auth_clients = auth_clients_dict['auth.reject']

        # When authentication has to be verified on entire
        # volume(not on sub-dirs) check if the required
        # clients names are listed in auth.reject option
        if 'all' in auth_dict:
            clients_list = auth_clients.split(',')
            res = all(elem in clients_list for elem in auth_dict['all'])
            if not res:
                self.logger.error("Authentication verification failed."
                                  f" auth.reject: {auth_clients}")
                return False
            self.logger.info("Authentication verified successfully. "
                             f"auth.reject: {auth_clients}")
            return True

        # When authentication has to be verified on sub-dirs,
        # convert the key-value pair to a format which matches
        # the value of auth.reject option
        for key, value in list(auth_dict.items()):
            auth_details.append(f"{key}({'|'.join(value)}")

        # Check if the required clients names are listed in
        # auth.reject option
        for auth_detail in auth_details:
            if auth_detail not in auth_clients:
                self.logger.error("Authentication verification failed."
                                  f" auth.reject: {auth_clients}")
                return False
        self.logger.info("Authentication verified successfully. "
                         f"auth.reject: {auth_clients}")
        return True

    def set_auth_reject(self, volname: str, server: str,
                        auth_dict: dict) -> bool:
        """
        Set auth reject for volumes or sub directories as required

        Args:
            volname(str): The name of volume in which auth.reject
                        has to be set
            server(str): IP or hostname of one node
            auth_dict(dict): key-value pair of dirs and clients list
                Example: auth_dict = {'/d1':['10.70.37.172',
                                             '10.70.37,173'],
                    '/d3/subd1':['10.70.37.172',
                                 'dh37-999.xyz.cdf.pqr.abc.com']}
                If authentication has to set on entire volume,
                use 'all' as key.
                    auth_dict = {'all': ['10.70.37.172',
                                         '10.70.37,173']}
                    auth_dict = {'all': ['*']}
                    'all' refer to entire volume
        Returns (bool):
            True if the auth.reject set operation is success,
            else False
        """
        auth_cmds = []
        if not auth_dict:
            self.logger.error("Authentication details are "
                              "not provided")
            return False

        # If authentication has to be set on sub-dirs,
        # convert the key-value pair to gluster
        # authentication set command format.
        if 'all' not in auth_dict:
            for key, value in list(auth_dict.items()):
                auth_cmds.append(f"{key}({'|'.join(value)})")
                auth_cmd = (f"gluster volume set {volname} "
                            f"auth.reject \"{','.join(auth_cmds)}\"")

        # When authentication has to be set on entire volume,
        # convert the key-value pair to gluster authentication
        # set command format
        else:
            auth_cmd = (f"gluster volume set {volname} "
                        f"auth.reject \"{','.join(auth_dict['all'])}\"")

        # Execute auth.allow setting on server.
        ret = self.execute_abstract_op_node(auth_cmd, server, False)
        if ret['error_code'] == 0 and self.verify_auth_reject(volname,
                                                              server,
                                                              auth_dict):
            self.logger.info("Auth reject set and verified successfully.")
            return True
        return False

    def authenticated_mount(self, volname: str, server: str,
                            mountpoint: str, client: str):
        """
        Mount volume on authenticated client

        Args:
            volname (str): Volume to be mounted
            server (str): Server to use for fetching thr volfile on client
            mountpoint (str): Path on which the volume has to be mounted
            client (str): Node on which mounting has to be done
        """
        # Mount volume
        cmd = f"mount.glusterfs {server}:/{volname} {mountpoint}"
        self.execute_abstract_op_node(cmd, client)

        # Verify mount
        ret = self.is_mounted(volname, mountpoint, client, server)
        if not ret:
            raise Exception("Unexpected: Volume is not mounted on client")

    def unauthenticated_mount(self, volname: str, server: str,
                              mountpoint: str, client: str):
        """
        Try to mount volume on unauthenticated client

        Args:
            volname (str): Volume to be mounted
            server (str): Server to use for fetching thr volfile on client
            mountpoint (str): Path on which the volume has to be mounted
            client (str): Node on which mounting has to be done
        """
        # Sometimes mount returns error code as 0, even though the mount
        # failed, so not checking the return value from volume_mount().
        # Mount volume
        cmd = f"mount.glusterfs {server}:/{volname} {mountpoint}"
        self.execute_abstract_op_node(cmd, client, False)

        # Verify mount
        ret = self.is_mounted(volname, mountpoint, client, server)
        if ret:
            # Mount operation did not fail as expected. Cleanup the mount.
            self.volume_unmount(volname, mountpoint, client)
            raise Exception("Mount operation did not fail as expected")

        self.logger.info("Mount operation failed as expected")

    def is_auth_failure(self, client: str,
                        previous_log_statement: str = '') -> str:
        """
        Check if the mount failure is due to authentication error
        Args:
            client(str): Client on which mount failure has to be verified.
            previous_log_statement(str): AUTH_FAILED message of previous mount
                failure due to auth error(if any). This is used to distinguish
                between the current and previous message.

        Return:
            str: Latest AUTH_FAILED event log message.
        """
        # Command to find the failure in log file
        cmd = "ls /var/log/glusterfs/ -1t | head -1"
        ret = self.execute_abstract_op_node(cmd, client)

        # Command to fetch latest AUTH_FAILED event log message.
        out = ret['msg'][0].rstrip('\n')
        cmd = f"grep AUTH_FAILED /var/log/glusterfs/{out} | tail -1"
        ret = self.execute_abstract_op_node(cmd, client)

        # Check whether the AUTH_FAILED log is of the latest mount failure
        if ret['msg'][0].rstrip('\n') == previous_log_statement:
            raise Exception("Mount failure is not due to authentication "
                            "error")

        return ret['msg'][0].rstrip('\n')
