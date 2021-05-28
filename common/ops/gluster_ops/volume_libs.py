"""
This file contains one class - VolumeOps which
holds volume related APIs which will be called
from the test case.
"""
from time import sleep
from collections import OrderedDict
from common.ops.abstract_ops import AbstractOps


class VolumeLibs(AbstractOps):
    """
    VolumeLibs class provides APIs to perform operations
    related to volumes like setup,cleanup and few others
    """

    def setup_volume(self, volname: str, node: str, conf_hash: dict,
                     server_list: list, brick_root: list,
                     force: bool = False, create_only: bool = False):
    	"""
        Setup the gluster volume with specified configuration
        Args:
            volname(str): volume name that has to be created
            node(str): server on which command has to be executed
            conf_hash (dict): Config hash providing parameters for volume
            				  creation.
            server_list (list): List of servers
            brick_root (list): List of root path of bricks
            force (bool): If this option is set to True, then create volume
            			  will get executed with force option.
            create_only (bool): True, if only volume creation is needed.
                           		False, will do volume create, start, set
	                            operation if any provided in the volume_config
	                            By default, value is set to False.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        """
		# Check if the volume already exists
	    vollist = self.get_volume_list(node)
	    if vollist is not None and volname in vollist:
	        self.logger.info(f"Volume {volname} already exists.")
	        return True

	    # Create volume
	    ret = self.volume_create(volname, node, conf_hash, server_list, brick_root,
	    				   		 force)
	    if create_only:
	    	return ret

	    # Allow sleep before volume start
	    sleep(2)

	    # Start volume
	    ret = self.volume_start(volname, node)

	    return ret
