"""
This file contains one class - GlusterfindOps which consists
of APIs related to glusterfind operation in gluster.
"""
from common.ops.abstract_ops import AbstractOps


class GlusterfindOps(AbstractOps):
    """
    GlusterfindOps class provides APIs to create, delete,
    list, pre, post and query glusterfind.
    """

    def gfind_create(self, node: str, volname: str, sessname: str,
                     debug: bool = False, resetsesstime: bool = False,
                     force: bool = False, excep: bool = True) -> dict:
        """
        Creates a glusterfind session for the given volume.

        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
            sessname (str): session name

        Optional:
            debug (bool): If this option is set to True, then
                        the command will be run with debug mode. If this
                        option is set to False, then the command will not
                        be run with debug mode.
            resetsesstime (bool): If this option is set to True, then the
                        session time will be forced to be reset to the current
                        time and the next incremental will start from this
                        time. If this option is set to False then the session
                        time will not be reset.
            force (bool): If this option is set to True, then glusterfind
                        create will get execute with force option. If it is
                        set to False, then glusterfind create will get
                        executed without force option.
            excep (bool): exception flag to bypass the exception if the
                        glusterfind create command fails. If set to False
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
            gfind_create("abc.com", testvol, testsession)
            >>> (0, 'Session testsession created with volume alpha\n', '')
        """

        params = ""
        if debug:
            params += " --debug"

        if resetsesstime:
            params += " --reset-session-time"

        if force:
            params += " --force"

        cmd = f"glusterfind create {sessname} {volname} {params}"
        return self.execute_abstract_op_node(cmd, node, excep)

    def gfind_delete(self, node: str, volname: str, sessname: str,
                     debug: bool = False, excep: bool = True) -> dict:
        """
        Deletes the given session

        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
            sessname (str): session name

        Optional:
            debug (bool): If this option is set to True, then the command
                        will be run with debug mode. If this option is set
                        to False, then the command will not be run with
                        debug mode.
            excep (bool): exception flag to bypass the exception if the
                        glusterfind delete command fails. If set to False
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
            gfind_delete("abc.com", testvol, testsession)
        """

        params = ""
        if debug:
            params += " --debug"

        cmd = f"glusterfind delete {sessname} {volname} {params}"
        return self.execute_abstract_op_node(cmd, node, excep)

    def gfind_list(self, node: str, volname: str = None,
                   sessname: str = None, debug: bool = False,
                   excep: bool = True) -> dict:
        """
        Lists the sessions created

        Args:
            node (str): Node on which cmd has to be executed.

        Optional:
            volname (str): volume name. If this option is provided then the
                        command will be run with the '--volume volname' option
            sessname (str): session name. If this option is provided then
                        the command will be run with the '--session sessname'
                        option.
            debug (bool): If this option is set to True, then the command will
                        be run with debug mode. If this option is set to
                        False, then the command will not be run with debug
                        mode.
            excep (bool): exception flag to bypass the exception if the
                        glusterfind list command fails. If set to False
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
            gfind_list("abc.com", testvol, testsession)
        """

        params = ""

        if not volname:
            volname = ""

        if volname:
            params += f" --volume {volname}"

        if not sessname:
            sessname = ""

        if sessname:
            params += f" --session {sessname}"

        if debug:
            params += " --debug"

        cmd = f"glusterfind list {params}"
        return self.execute_abstract_op_node(cmd, node, excep)

    def gfind_pre(self, node: str, volname: str, sessname: str,
                  outfile: str = "", excep: bool = True, **kwargs) -> dict:
        """
        Retrieve the modified files and directories and store it in the
        outfile.

        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
            sessname (str): session name

        Optional:
            outfile (str): This is the incremental list of modified files.
            excep (bool): exception flag to bypass the exception if the
                        glusterfind pre command fails. If set to False
                        the exception is bypassed and value from remote
                        executioner is returned. Defaults to True

        Kwargs:
            **kwargs: The keys, values in kwargs are:
                    - full: (bool)|False
                    - tagforfullfind: (str)|None
                    - gftype: (str)|None
                    - outprefix: (str)|None
                    - fieldsep: (str)|None
                    - debug: (bool)|False
                    - noencode: (bool)|False
                    - disablepartial: (bool)|False
                    - namespace: (bool)|False
                    - regenoutfile: (bool)|False

                Where:
                full (bool): If this option is set to True, then the command
                    will be run with '--full' option and a full find will be
                    performed. Else, without it.
                tagforfullfind (str): When running the command with '--full'
                    option, a subset of files can be retrieved according to
                    a tag.
                gftype (str): 'Type' option specifies the finding the list of
                    files or directories only. If the value is set to 'f' then
                    only the file types will be listed. If the value is set to
                    'd' then only the directory types will be listed. If the
                    value is set to 'both' then the files and directories both
                    will be listed.
                outprefix (str): Prefix to the path/name specified in the
                    outfile.
                fieldsep (str): field-separator specifies the character/s that
                    glusterfind output uses to separate fields
                debug (bool): If this option is set to True, then the command
                    will be run with debug mode. If this option is set to
                    False, then the command will not be run with debug mode.
                noencode (bool): If this option is set to True, then it
                    disables encoding of file paths. If this option is set to
                    False, thenthe command will run without --no-encode option
                disablepartial (bool): If this option is set to True, then the
                    partial-find feature will be disabled. If this option is
                    set to False, then the default value will be respected.
                namespace (bool): If this option is set to True, then the
                    command will be run with '--N' option and only namespace
                    changes will be listed. If this option is set to False,
                    then the command will be run without the '--N' option.
                regenoutfile (bool): If this option is set to True, then the
                    outfile will be regenerated. If this option is set to
                    False, then the outfile will not be regenerated.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
            None: If wrong params are passed

        Example:
            gfind_pre("abc.com", testvol, testsession, outfile=/newoutfile.txt)
        """

        outprefix = fieldsep = tagforfullfind = gftype = None
        full = debug = noencode = disablepartial = regenoutfile = False
        namespace = False
        params = ""

        if "outprefix" in kwargs:
            outprefix = str(kwargs["outprefix"])

        if "fieldsep" in kwargs:
            fieldsep = str(kwargs["fieldsep"])

        if "full" in kwargs:
            full = bool(kwargs["full"])

        if "tagforfullfind" in kwargs:
            tagforfullfind = str(kwargs["tagforfullfind"])

        if "gftype" in kwargs:
            gftype = str(kwargs["gftype"])

        if "debug" in kwargs:
            debug = bool(kwargs["debug"])

        if "noencode" in kwargs:
            noencode = bool(kwargs["noencode"])

        if "disablepartial" in kwargs:
            disablepartial = bool(kwargs["disablepartial"])

        if "regenoutfile" in kwargs:
            regenoutfile = bool(kwargs["regenoutfile"])

        if "namespace" in kwargs:
            namespace = bool(kwargs["namespace"])

        if outfile == "":
            self.logger.error("Invalid command: Outfile needs to be provided"
                              "in order for the pre command to run")
            return None

        if outfile != "":
            params += f" {outfile}"

        if outprefix:
            params += f" --output-prefix {outprefix}"

        if fieldsep:
            params += f" --field-separator '{fieldsep}'"

        if not full and gftype:
            if gftype == "both":
                params += " --type both"
            else:
                self.logger.error("Invalid command: The '--type' option with"
                                  " 'f' or 'd' as values can only be used "
                                  "along with '--full' option")
                return None

        if not gftype:
            gftype = ""

        if full:
            params += " --full"

            gftypelist = ["f", "d", "both", ""]
            if gftype in gftypelist:
                if gftype != "":
                    params += f" --type {gftype}"
            else:
                self.logger.error("Invalid value for the '--type' option of"
                                  "the glusterfind pre command. Choose among"
                                  " 'f/d/both'")
                return None

            if tagforfullfind:
                params += f" --tag-for-full-find {tagforfullfind}"

        if debug:
            params += " --debug"

        if noencode:
            params += " --no-encode"

        if disablepartial:
            params += " --disable-partial"

        if regenoutfile:
            params += " --regenerate-outfile"

        if namespace:
            params += " -N"

        cmd = f"glusterfind pre {sessname} {volname} {params}"
        return self.execute_abstract_op_node(cmd, node, excep)

    def gfind_post(self, node: str, volname: str, sessname: str,
                   debug: bool = False, excep: bool = True) -> dict:
        """
        Run to update the session time

        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
            sessname (str): session name

        Optional:
            debug (bool): If this option is set to True, then the command
                        will be run with debug mode. Else, it will not run
                        in debug mode.
            excep (bool): exception flag to bypass the exception if the
                        glusterfind post command fails. If set to False
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
            gfind_post("abc.com", testvol, testsession)
        """

        params = ""
        if debug:
            params += " --debug"

        cmd = f"glusterfind post {sessname} {volname} {params}"
        return self.execute_abstract_op_node(cmd, node, excep)

    def gfind_query(self, node: str, volname: str, outfile: str = "",
                    since: str = "", end: str = "", excep: bool = True,
                    **kwargs) -> dict:
        """
        Get a list of changed files based on a specific timestamp.

        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
            outfile (str): This is the incremental list of modified files.

        Optional:
            since (int): Timestamp from which the files need to be retrieved.
            end (int): Timestamp until which the files need to be retrieved.
            excep (bool): exception flag to bypass the exception if the
                        glusterfind query command fails. If set to False
                        the exception is bypassed and value from remote
                        executioner is returned. Defaults to True

        Kwargs:
            **kwargs: The keys, values in kwargs are:
                    - full: (bool)|False
                    - tagforfullfind: (str)|None
                    - gftype: (str)|None
                    - outprefix: (str)|None
                    - fieldsep: (str)|None
                    - debug: (bool)|False
                    - noencode: (bool)|False
                    - disablepartial: (bool)|False
                    - namespace: (bool)|False

            Where:
            full (bool): If this option is set to True, then the command
                    will be run with '--full' option and a full find will be
                    performed. Else, without it.
            tagforfullfind (str): When running the command with '--full'
                option, a subset of files can be retrieved according to
                a tag.
            gftype (str): 'Type' option specifies the finding the list of
                files or directories only. If the value is set to 'f' then
                only the file types will be listed. If the value is set to
                'd' then only the directory types will be listed. If the
                value is set to 'both' then the files and directories both
                will be listed.
            outprefix (str): Prefix to the path/name specified in the
                outfile.
            fieldsep (str): field-separator specifies the character/s that
                glusterfind output uses to separate fields
            debug (bool): If this option is set to True, then the command
                will be run with debug mode. If this option is set to
                False, then the command will not be run with debug mode.
            noencode (bool): If this option is set to True, then it
                disables encoding of file paths. If this option is set to
                False, thenthe command will run without --no-encode option
            disablepartial (bool): If this option is set to True, then the
                partial-find feature will be disabled. If this option is
                set to False, then the default value will be respected.
            namespace (bool): If this option is set to True, then the
                command will be run with '--N' option and only namespace
                changes will be listed. If this option is set to False,
                then the command will be run without the '--N' option.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
            None: If wrong params are passed

        Example1:
            gfind_query("abc.com", testvol, outfile=/newoutfile.txt,
                        since=timestamp1, end=timestamp2, full=False)
        Example2:
            gfind_query("abc.com", testvol, outfile=/newoutfile.txt,
                        gftype='f')
                The above example will fail because the
                'full' option is not provided.
        """

        outprefix = fieldsep = tagforfullfind = gftype = None
        full = debug = noencode = disablepartial = namespace = False
        params = ""

        if "outprefix" in kwargs:
            outprefix = str(kwargs["outprefix"])

        if "fieldsep" in kwargs:
            fieldsep = str(kwargs["fieldsep"])

        if "full" in kwargs:
            full = bool(kwargs["full"])

        if "tagforfullfind" in kwargs:
            tagforfullfind = str(kwargs["tagforfullfind"])

        if "gftype" in kwargs:
            gftype = str(kwargs["gftype"])

        if "debug" in kwargs:
            debug = bool(kwargs["debug"])

        if "noencode" in kwargs:
            noencode = bool(kwargs["noencode"])

        if "disablepartial" in kwargs:
            disablepartial = bool(kwargs["disablepartial"])

        if "namespace" in kwargs:
            namespace = bool(kwargs["namespace"])

        if full and since != "" and end != "":
            self.logger.error("Invalid command: Glusterfind query accepts"
                              " either full or the since/end timestamps")
            return None

        if outfile == "":
            self.logger.error("Invalid command: Outfile needs to be provided"
                              " for the query command to run")
            return None

        if outfile != "":
            params += f" {outfile}"

        if not full:
            if since != "":
                params += f" --since-time {since}"
            if end != "":
                params += f" --end-time {end}"
            if gftype:
                if gftype == "both":
                    params += " --type both"
                else:
                    self.logger.error("Invalid command: The '--type' option "
                                      "with 'f' or 'd' as values can only be"
                                      " used along with '--full' option")
                    return None

        if not gftype:
            gftype = ""

        if full:
            params += " --full"

            gftypelist = ["f", "d", "both", ""]
            if gftype in gftypelist:
                if gftype != "":
                    params += f" --type {gftype}"
            else:
                self.logger.error("Invalid value for the '--type' option of"
                                  " the glusterfind query command. Choose "
                                  "among 'f/d/both'.")
                return None

            if tagforfullfind:
                params += f" --tag-for-full-find {tagforfullfind}"

        if outprefix:
            params += f" --output-prefix {outprefix}"

        if fieldsep:
            params += f" --field-separator '{fieldsep}'"

        if debug:
            params += " --debug"

        if noencode:
            params += " --no-encode"

        if disablepartial:
            params += " --disable-partial"

        if namespace:
            params += " -N"

        cmd = f"glusterfind query {volname} {params}"
        return self.execute_abstract_op_node(cmd, node, excep)
