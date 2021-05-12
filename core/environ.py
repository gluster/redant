import sys
from socket import timeout
import traceback
import paramiko
sys.path.insert(1, ".")
from common.mixin import RedantMixin


class environ:
    """
    Framework level control on the gluster environment. Controlling both
    the setup and the complete cleanup.
    """

    def __init__(self, param_obj, log_path: str, log_level: str):
        """
        Redant mixin obj to be used for server setup and teardown operations
        has to be created.
        """
        self.redant = RedantMixin(param_obj.get_server_config())
        self.redant.init_logger("environ", log_path, log_level)
        try:
            self.redant.establish_connection()
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            print(f'''
            It seems one of the nodes is down.
            Message: {e}.
            Check and run again.
            ''')
            sys.exit(0)
        except paramiko.ssh_exception.AuthenticationException as e:
            print(f"""
            Authentication failed.
            Message: {e}
            Check and run again.
            """)

            sys.exit(0)
        except timeout as e:
            print(f"""
            Oops! There was a timeout connecting the servers.
            Message:{e}
            Check and run again.
            """)

            sys.exit(0)
        except Exception as e:
            print(e)
            sys.exit(0)

        self.server_list = param_obj.get_server_ip_list()

    def setup_env(self):
        """
        Setting up of the environment before the TC execution begins.
        """
        try:
            self.redant.start_glusterd()
            self.redant.create_cluster(self.server_list)
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
            sys.exit(0)

    def teardown_env(self):
        """
        The teardown of the complete environment once the test framework
        ends.
        """
