"""
Copyright (C) 2017-2020  Red Hat, Inc. <http://www.redhat.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

Description:
Test Case in this module is related to Gluster volume get functionality
"""

# nonDisruptive;dist,rep,dist-rep,disp,dist-disp

from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):

    def run_test(self, redant):
        """
        1. Create a gluster cluster
        2. Get the option from the non-existing volume,
        gluster volume get <non-existing vol> io-cache
        3. Get all options from the non-existing volume,
        gluster volume get <non-existing volume > all
        4. Provide a incorrect command syntax to get the options
        from the volume
            gluster volume get <vol-name>
            gluster volume get
            gluster volume get io-cache
        5. Create any type of volume in the cluster
        6. Get the value of the non-existing option
            gluster volume get <vol-name> temp.key
        7. get all options set on the volume
            gluster volume get <vol-name> all
        8. get the specific option set on the volume
            gluster volume get <vol-name> io-cache
        9. Set an option on the volume
            gluster volume set <vol-name> performance.low-prio-threads 14
        10. Get all the options set on the volume and check
        for low-prio-threads
            gluster volume get <vol-name> all then get the
            low-prio-threads value
        11. Get all the options set on the volume
                gluster volume get <vol-name> all
        12.  Check for any cores in "cd /"
        """

        # time stamp of current test case
        ret = redant.execute_abstract_op_node('date +%s',
                                              self.server_list[0])
        test_timestamp = ret['msg'][0].strip()
        # performing gluster volume get command for non exist volume io-cache
        self.non_exist_volume = "abc99"
        cmd = f"gluster volume get {self.non_exist_volume} io-cache"
        ret = redant.execute_abstract_op_node(cmd,
                                              self.server_list[0],
                                              False)
        if ret['error_code'] == 0:
            raise Exception(f"gluster volume get command should fail "
                            f"for non existing volume with io-cache "
                            f"option :{self.non_exist_volume}")
        err = ret['error_msg']
        msg = ('Volume ' + self.non_exist_volume + ' does not exist')

        if msg not in err:
            raise Exception(f"No proper error message for non existing "
                            f"volume with io-cache option :"
                            f"{self.non_exist_volume}")

        redant.logger.info(f"gluster volume get command failed successfully "
                           f"for non-existing volume with io-cache option"
                           f":{self.non_exist_volume}")

        # performing gluster volume get all command for non exist volume
        cmd = f"gluster volume get {self.non_exist_volume} all"
        ret = redant.execute_abstract_op_node(cmd,
                                              self.server_list[0],
                                              False)
        if ret['error_code'] == 0:
            raise Exception(f"gluster volume get command should fail "
                            f"for non existing volume with all "
                            f"option :{self.non_exist_volume}")
        err = ret['error_msg']
        if msg not in err:
            raise Exception(f"No proper error message for non existing "
                            f"volume with all option :"
                            f"{self.non_exist_volume}")
        redant.logger.info(f"gluster volume get command failed successfully "
                           f"for non-existing volume with all option"
                           f":{self.non_exist_volume}")

        # performing gluster volume get command for non exist volume
        cmd = f"gluster volume get {self.non_exist_volume}"
        ret = redant.execute_abstract_op_node(cmd,
                                              self.server_list[0],
                                              False)
        if ret['error_code'] == 0:
            raise Exception(f"gluster volume get command should fail "
                            f"for non existing volume"
                            f": {self.non_exist_volume}")
        err = ret['error_msg']
        msg = 'get <VOLNAME|all> <key|all>'

        if msg not in err:
            raise Exception(f"No proper error message for non existing "
                            f"volume {self.non_exist_volume}")
        redant.logger.info(f"gluster volume get command failed "
                           f"successfully for non-existing"
                           f" volume :{self.non_exist_volume}")

        # performing gluster volume get command without any volume name given
        cmd = "gluster volume get"
        ret = redant.execute_abstract_op_node(cmd,
                                              self.server_list[0],
                                              False)
        if ret['error_code'] == 0:
            raise Exception("gluster volume get command should fail "
                            "for non existing volume")
        err = ret['error_msg']

        if msg not in err:
            raise Exception("No proper error message for gluster "
                            "volume get command")
        redant.logger.info("gluster volume get command failed successfully")

        # performing gluster volume get io-cache command
        # without any volume name given
        cmd = "gluster volume get io-cache"
        ret = redant.execute_abstract_op_node(cmd,
                                              self.server_list[0],
                                              False)
        if ret['error_code'] == 0:
            raise Exception("gluster volume get io-cache command "
                            "should fail")
        if msg not in err:
            raise Exception("No proper error message for gluster volume "
                            "get io-cache command")
        redant.logger.info("gluster volume get io-cache "
                           "command failed successfully")

        # gluster volume get volname with non existing option
        cmd = f"gluster volume get {self.vol_name} temp.key"
        ret = redant.execute_abstract_op_node(cmd,
                                              self.server_list[0],
                                              False)
        if ret['error_code'] == 0:
            raise Exception(f"gluster volume get command should fail "
                            f"for existing volume {self.vol_name} "
                            f"with non-existing option")
        msg = 'Did you mean auth.allow or ...reject?'
        err = ret['error_msg']
        if msg not in err:
            msg = 'volume get option: failed: Did you mean ctime.noatime?'
        if msg not in err:
            raise Exception(f"No proper error message for existing "
                            f"volume {self.vol_name}"
                            f" with non-existing option")

        redant.logger.info(f"gluster volume get command failed "
                           f"successfully for existing volume "
                           f"{self.vol_name} with non existing option")

        # performing gluster volume get volname all
        ret = redant.get_volume_options(self.vol_name, "all",
                                        self.server_list[0])
        if ret is None:
            raise Exception(f"gluster volume get {self.vol_name} "
                            f"all command failed")

        # performing gluster volume get volname io-cache
        ret = redant.get_volume_options(self.vol_name, "io-cache",
                                        self.server_list[0])
        if ret is None:
            raise Exception(f"gluster volume get {self.vol_name} "
                            f"io-cache command failed")
        ver = redant.get_gluster_version(self.server_list[0])

        if float(ver) >= 6.0:

            if ret['performance.io-cache'] not in ['on', 'off']:
                raise Exception("io-cache value is not correct")
        redant.logger.info("io-cache value is correct")

        # Performing gluster volume set volname performance.low-prio-threads
        prio_thread = {'performance.low-prio-threads': '14'}
        redant.set_volume_options(self.vol_name,
                                  prio_thread,
                                  self.server_list[0])

        # Performing gluster volume get all, checking low-prio threads value
        ret = redant.get_volume_options(self.vol_name, "all",
                                        self.server_list[0])
        if ret is None:
            raise Exception(f"gluster volume get {self.vol_name} "
                            f"all failed")
        lp_threads = ret['performance.low-prio-threads']
        if "14" not in lp_threads:
            raise Exception("performance.low-prio-threads value is "
                            "not correct")

        redant.logger.info("performance.low-prio-threads value is correct")

        # performing gluster volume get volname all
        ret = redant.get_volume_options(self.vol_name, "all",
                                        self.server_list[0])
        if ret is None:
            raise Exception(f"gluster volume get {self.vol_name} "
                            f"all failed")

        # Checking core file created or not in "/" directory
        ret = redant.check_core_file_exists(self.server_list, test_timestamp)
        if not ret:
            redant.logger.info("No core file found, glusterd service "
                               "running successfully")
        else:
            raise Exception("core file found in directory, it "
                            "indicates the glusterd service crash")
