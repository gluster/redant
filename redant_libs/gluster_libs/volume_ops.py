"""
This file contains one class - VolumeOps which
holds volume related APIs which will be called
from the test case.
"""


class VolumeOps:
    """
    VolumeOps class provides APIs to perform operations
    related to volumes like create,delete,start,stop,
    fetch information.
    """

    def volume_create(self, node: str, volname: str,
                      bricks_list: list, force: bool = False,
                      **kwargs):
        """
        Create the gluster volume with specified configuration
        Args:
            node(str): server on which command has to be executed
            volname(str): volume name that has to be created
            bricks_list (list): List of bricks to use for creating volume.

        Kwargs:
            force (bool): If this option is set to True, then create volume
                will get executed with force option. If it is set to False,
                then create volume will get executed without force option
            **kwargs
                The keys, values in kwargs are:
                    - replica_count : (int)|None
                    - arbiter_count : (int)|None
                    - stripe_count : (int)|None
                    - disperse_count : (int)|None
                    - disperse_data_count : (int)|None
                    - redundancy_count : (int)|None
                    - transport_type : tcp|rdma|tcp,rdma|None
                    - ...
        """

        replica = arbiter = stripe = disperse = disperse_data = redundancy = ''
        transport = ''

        if 'replica_count' in kwargs:
            replica = f"replica {kwargs['replica_count']}"

        if 'arbiter_count' in kwargs:
            arbiter = f"arbiter {kwargs['arbiter_count']}"

        if 'stripe_count' in kwargs:
            stripe = f"stripe {kwargs['stripe_count']}"

        if 'disperse_count' in kwargs:
            disperse = f"disperse {kwargs['disperse_count']}"

        if 'disperse_data_count' in kwargs:
            disperse = f"disperse-data {kwargs['disperse_data_count']}"

        if 'redundancy_count' in kwargs:
            redundancy = f"redundancy {kwargs['redundancy_count']}"

        if 'transport_type' in kwargs:
            transport = f"transport {kwargs['transport_type']}"

        cmd = (f"gluster volume create {volname} {replica} "
               f"{arbiter} {stripe} {disperse} {disperse_data} "
               f"{redundancy} {transport} {' '.join(bricks_list)} --xml "
               "--mode=script")

        if force:
            cmd = cmd + " force"

        self.rlog(f"Running {cmd} on node {node}")

        ret = self.execute_command(node=node, cmd=cmd)

        if int(ret['msg']['opRet']) != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog(f"Successfully ran {cmd} on {node}")

    def volume_start(self, node: str, volname: str, force: bool = False):
        """
        Starts the gluster volume
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
        Kwargs:
            force (bool): If this option is set to True, then start volume
                will get executed with force option. If it is set to False,
                then start volume will get executed without force option
        """

        if force:
            cmd = f"gluster volume start {volname} force --mode=script --xml"
        else:
            cmd = f"gluster volume start {volname} --mode=script --xml"

        self.rlog(f"Running {cmd} on node {node}")

        ret = self.execute_command(node=node, cmd=cmd)

        if int(ret['msg']['opRet']) != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog(f"Successfully ran {cmd} on {node}")

    def volume_stop(self, node: str, volname: str, force: bool = False):
        """
        Stops the gluster volume
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
        Kwargs:
            force (bool): If this option is set to True, then start volume
                will get executed with force option. If it is set to False,
                then start volume will get executed without force option
        """

        if force:
            cmd = f"gluster volume stop {volname} force --mode=script --xml"
        else:
            cmd = f"gluster volume stop {volname} --mode=script --xml"

        self.rlog(f"Running {cmd} on node {node}")

        ret = self.execute_command(node=node, cmd=cmd)

        if int(ret['msg']['opRet']) != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog(f"Successfully ran {cmd} on {node}")

    def volume_delete(self, node: str, volname: str):
        """
        Deletes the gluster volume if given volume exists in
        gluster.
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
        """

        cmd = f"gluster volume delete {volname} --mode=script --xml"

        self.rlog(f"Running {cmd} on node {node}")

        ret = self.execute_command(node=node, cmd=cmd)

        if int(ret['msg']['opRet']) != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog(f"Successfully ran {cmd} on {node}")

    def volume_info(self, node: str, volname: str = 'all') -> dict:
        """
        Gives volume information
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
        Returns:
            a dictionary with volume information.
        """

        cmd = f"gluster volume info {volname} --xml"

        self.rlog(f"Running {cmd} on node {node}")

        ret = self.execute_command(node=node, cmd=cmd)

        if int(ret['msg']['opRet']) != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog(f"Successfully ran {cmd} on {node}")

        volume_info = ret['msg']

        ret_val = volume_info['volInfo']['volumes']['volume']

        return ret_val
