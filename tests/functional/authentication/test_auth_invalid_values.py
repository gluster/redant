"""
 Copyright (C) 2017-2018  Red Hat, Inc. <http://www.redhat.com>

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
    TC to tests negative scenario of authentication feature by giving
    invalid values.
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp
# TODO: Add nfs
from tests.d_parent_test import DParentTest


class TestAuthInvalidValues(DParentTest):

    def _set_invalid_auth(self, auth_opt, values_list):
        """
        Try to set invalid values on authentication options.
        """
        error_msg_fuse = "not a valid internet-address-list"
        # NFS not supported, yet
        # error_msg_nfs = "not a valid mount-auth-address"

        # Try to set invalid values.
        for value in values_list:
            auth_cmd = (f"gluster volume set {self.vol_name} {auth_opt} "
                        f"\"{value}\"")
            ret = self.redant.execute_abstract_op_node(auth_cmd,
                                                       self.server_list[0],
                                                       False)
            if ret['error_code'] == 0:
                raise Exception(f"Command to set {auth_opt} value as {value}"
                                " didn't fail as expected.")

            # NFS not yet supported
            # Verify whether the failure is due to invalid value.
            # if self.mount_type == "nfs":
            #     if error_msg_nfs not in err:
            #         g.log.error("Command to set %s value as %s has failed"
            #                     " due to unknown reason.", auth_opt, value)
            #         return False

            # Uncomment below check after NFS is supported
            # if self.mount_type == "glusterfs":
            if error_msg_fuse not in ret['error_msg']:
                self.redant.logger.error(f"Command to set {auth_opt} value"
                                         f" as {value} has failed due to "
                                         "unknown reason.")
                return False

            self.redant.logger.info(f"Expected: Command to set {auth_opt} "
                                    f"value as {value} has failed due to "
                                    "invalid value.")
        return True

    def run_test(self, redant):
        """
        Verify negative scenario in authentication allow and reject options by
        trying to set invalid values.
        Steps:
        1. Create and start volume.
        2. Try to set the value "a/a", "192.{}.1.2", "/d1(a/a)",
           "/d1(192.{}.1.2)" separately in auth.allow option.
        3. Try to set the value "a/a", "192.{}.1.2", "/d1(a/a)",
           "/d1(192.{}.1.2)" separately in auth.reject option.
        4. Steps 2 and 3 should fail due to error "not a valid
           internet-address-list"
        -------------------------
        Not yet implemented
        -------------------------
        5. Verify volume is exported as nfs.
        6. Try to set the value "a/a", "192.{}.1.2", "/d1(a/a)",
           "/d1(192.{}.1.2)" separately in nfs.rpc-auth-allow option.
        7. Try to set the value "a/a", "192.{}.1.2", "/d1(a/a)",
           "/d1(192.{}.1.2)" separately in nfs.rpc-auth-reject option.
        8. Steps 6 and 7 should fail due to error "not a valid
           mount-auth-address"
        """
        # pylint: disable = unused-argument
        invalid_values = ["a/a", "192.{}.1.2", "/d1(a/a)", "/d1(192.{}.1.2)"]

        # Try to set invalid values in auth.allow option.
        ret = self._set_invalid_auth("auth.allow", invalid_values)
        if not ret:
            raise Exception("Failure of command to set auth.allow value "
                            "is not because of invalid values.")

        # Try to set invalid values in auth.reject option.
        ret = self._set_invalid_auth("auth.reject", invalid_values)
        if not ret:
            raise Exception("Failure of command to set auth.reject value"
                            " is not because of invalid values.")

        # Uncomment and update the TC after NFS is supported in Redant
        # if self.mount_type == "nfs":
        #     # Check whether volume is exported as gnfs
        #     ret = is_volume_exported(self.mnode, self.volname,
        #                              self.mount_type)
        #     self.assertTrue(ret, "Volume is not exported as nfs")

        #     # Enable nfs.addr-namelookup option.
        #     ret = set_volume_options(self.mnode, self.volname,
        #                              {"nfs.addr-namelookup": "enable"})
        #     self.assertTrue(ret, "Failed to enable nfs.addr-namelookup "
        #                          "option.")

        #     # Try to set invalid values in nfs.rpc-auth-allow option.
        #     ret = self.set_invalid_auth("nfs.rpc-auth-allow", invalid_values)
        #     self.assertTrue(ret, "Command failure to set nfs.rpc-auth-allow"
        #                          " value is not because of invalid values.")
        #     g.log.info("Successfully verified nfs.rpc-auth-allow set command"
        #                " using invalid values. Command failed as expected.")

        #     # Try to set invalid values in nfs.rpc-auth-reject option.
        #     self.set_invalid_auth("nfs.rpc-auth-reject", invalid_values)
        #     self.assertTrue(ret, "Command failure to set nfs.rpc-auth-reject"
        #                          " value is not because of invalid values.")
        #     g.log.info("Successfully verified nfs.rpc-auth-reject set "
        #                "command using invalid values. Command failed "
        #                "as expected.")
