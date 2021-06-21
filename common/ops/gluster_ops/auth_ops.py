"""
Auth ops module deals with the aut allow and reject operations
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
        ret = self.execute_abstract_op_node(auth_cmd, server)
        if not ret and self.verify_auth_allow(volname, server, auth_dict):
            self.logger.info("Authentication set and verified successfully.")
            return True

        return False
