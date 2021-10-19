"""
    This module deals with memory and cpu logging
"""
import numpy as np
import pandas as pd

from common.ops.abstract_ops import AbstractOps


class MemoryAndCpuOps(AbstractOps):
    """
    Class which is responsible for memory and cpu logging
    """
    def _start_logging_processes(self, process: str, servers: list,
                                 test_name: str, interval: int,
                                 count: int) -> list:
        """Start logging processes on all nodes for a given process

        Args:
        process(str): glusterfs process for which logging is done
        servers(list): Servers on which CPU and memory usage has to be logged
        test_name(str): Name of testcase for which logs are to be collected
        interval(int): Time interval after which logs are to be collected
        count(int): Number of samples to be captured

        Returns:
        list: A list of logging processes
        """
        if not isinstance(servers, list):
            servers = [servers]

        cmd = ("python3 /usr/share/redant/script/memory_and_cpu_logger.py"
               f" -p {process} -t {test_name} -i {interval} -c {count}")
        logging_process = []
        for server in servers:
            self.logger.debug(f"Start logging for {process} on {server}")
            proc = self.execute_command_async(cmd, server)
            logging_process.append(proc)
        return logging_process

    def log_memory_and_cpu_usage_on_servers(self, servers: list,
                                            test_name: str, interval: int = 60,
                                            count: int = 100) -> dict:
        """Log memory and CPU usage of gluster server processes

        Args:
         servers(list): Servers on which CPU and memory usage has to be logged
         test_name(str): Name of the testcase for which logs to be collected
        Optional:
         interval(int): Time interval after which logs are to be collected
                        (Default:60)
         count(int): Number of samples to be captured (Default:100)

        Returns:
         dict: Logging processes dict for all gluster server processes
        """
        logging_process_dict = {}
        for proc_name in ('glusterd', 'glusterfs', 'glusterfsd'):
            logging_procs = self._start_logging_processes(proc_name, servers,
                                                          test_name, interval,
                                                          count)
            logging_process_dict[proc_name] = logging_procs
        return logging_process_dict

    def log_memory_and_cpu_usage_on_clients(self, servers: list,
                                            test_name: str, interval: int = 60,
                                            count: int = 100) -> dict:
        """Log memory and CPU usage of gluster client processes

        Args:
         servers(list): Clients on which CPU and memory usage has to be logged
         test_name(str): Name of testcase for which logs are to be collected
        Optional:
         interval(int): Time interval after which logs are to be collected
                        (Defaults:60)
         count(int): Number of samples to be captured (Default:100)

        Returns:
         dict: Logging processes dict for all gluster client processes
        """
        logging_process_dict = {}
        logging_procs = self._start_logging_processes('glusterfs', servers,
                                                      test_name, interval,
                                                      count)
        logging_process_dict['glusterfs'] = logging_procs
        return logging_process_dict

    def log_memory_and_cpu_usage_on_cluster(self, server: list, client: list,
                                            test_name: str, interval: int = 60,
                                            count: int = 100) -> dict:
        """Log memory and CPU usage on gluster cluster

        Args:
         server(list): Servers on which memory and CPU usage is to be logged
         client(list): Clients on which memory and CPU usage is to be logged
         test_name(str): Name of testcase for which logs are to be collected
        Optional:
         interval(int): Time interval after which logs are to be collected
                        (Default:60)
         count(int): Number of samples to be captured (Default:100)

        Returns:
         dict: Logging processes dict for all servers and clients
        """
        # Start logging on all servers
        server_logging_processes = (self.log_memory_and_cpu_usage_on_servers(
                                    server, test_name, interval, count))
        if not server_logging_processes:
            self.logger.error("server logging process is empty")
            return {}

        # Starting logging on all clients
        client_logging_processes = (self.log_memory_and_cpu_usage_on_clients(
                                    client, test_name, interval, count))
        if not client_logging_processes:
            self.logger.error("client logging process is empty")
            return {}

        # Combining dicts
        logging_process_dict = {}
        for node_type, proc_dict in (('server', server_logging_processes),
                                     ('client', client_logging_processes)):
            logging_process_dict[node_type] = {}
            for proc in proc_dict:
                logging_process_dict[node_type][proc] = (proc_dict[proc])
        return logging_process_dict

    def wait_for_logging_processes_to_stop(self, proc_dict: dict,
                                           cluster: bool = False) -> bool:
        """Wait for all given logging processes to stop

        Args:
         proc_dict(dict): Dictionary of all the active logging processes

        Optional:
         cluster(bool): True if proc_dict is for the entire cluster else False
                        (Default:False)

        Retruns:
         bool: True if processes are completed else False
        """
        flag = []
        if cluster:
            for sub_dict in proc_dict:
                for proc_name in proc_dict[sub_dict]:
                    for proc in proc_dict[sub_dict][proc_name]:
                        self.logger.debug(f"Waiting for {proc} logging "
                                          "process to stop")
                        self.wait_till_async_command_ends(proc)
                        flag.append(True)
        else:
            for proc_name in proc_dict:
                for proc in proc_dict[proc_name]:
                    self.logger.debug(f"Waiting for {proc} logging "
                                      "process to stop")
                    self.wait_till_async_command_ends(proc)
                    flag.append(True)
        return all(flag)

    def _check_for_oom_killers(self, nodes: list, process: str,
                               oom_killer_list: list):
        """Checks for OOM killers for a specific process

        Args:
         nodes(list): Nodes on which OOM killers have to be checked
         process(str): Process for which OOM killers have to be checked
         oom_killer_list(list): A list in which the presence of
                                OOM killer has to be noted
        """
        if not isinstance(nodes, list):
            nodes = [nodes]

        cmd = ("grep -i 'killed process' /var/log/messages* "
               f"| grep -w '{process}'")
        self.logger.debug(f"Checking for oom killers for {process} process"
                          " on {nodes}")
        ret_codes = self.execute_abstract_op_multinode(cmd, nodes, False)
        for ret in ret_codes:
            if ret['error_code'] == 0:
                self.logger.error(f'OOM killer observed on node for {process}')
                self.logger.error(ret['msg'])
                oom_killer_list.append(True)
            else:
                oom_killer_list.append(False)

    def check_for_oom_killers_on_servers(self, nodes: list) -> bool:
        """Check for OOM killers on servers

        Args:
         nodes(list): Servers on which OOM kills have to be checked

        Returns:
         bool: True if OOM killers are present on any server else False
        """
        oom_killer_list = []
        for process in ('glusterfs', 'glusterfsd', 'glusterd'):
            self._check_for_oom_killers(nodes, process, oom_killer_list)
        return any(oom_killer_list)

    def check_for_oom_killers_on_clients(self, nodes: list) -> bool:
        """Check for OOM killers on clients

        Args:
         nodes(list): Clients on which OOM kills have to be checked

        Returns:
         bool: True if OOM killers are present on any client else false
        """
        oom_killer_list = []
        self._check_for_oom_killers(nodes, 'glusterfs', oom_killer_list)
        return any(oom_killer_list)

    def create_dataframe_from_csv(self, node: str, proc_name: str,
                                  test_name: str):
        """Creates a dataframe from a given process.

        Args:
         node(str): Node from which csv is to be picked
         proc_name(str): Name of process for which csv is to picked
         test_name(str): Name of the testcase for which CSV

        Returns:
         dataframe: Pandas dataframe if CSV file exits else None
        """
        # Read the csv file generated by memory_and_cpu_logger.py
        ret = self.execute_abstract_op_node(f"cat /root/{proc_name}.csv", node)
        if ret['error_code'] != 0:
            self.logger.error("Cannot read the csv file")
            return None

        raw_data = ret['msg']
        # Split the complete dump to individual lines
        data = []
        for i in raw_data:
            data.append(i.split("\r\n")[0])
        rows, flag = [], False
        for line in data:
            values = line.split(',')
            if test_name == values[0]:
                # Reset rows if it's the second instance
                if flag:
                    rows = []
                flag = True
                continue

            # Pick and append values which have complete entry
            if flag and len(values) == 4:
                rows.append(values)

        # Create a panda dataframe and set the type for columns
        dataframe = pd.DataFrame(rows[1:], columns=rows[0])
        conversion_dict = {'Process ID': int,
                           'CPU Usage': float,
                           'Memory Usage': float}
        dataframe = dataframe.astype(conversion_dict)
        return dataframe

    def _perform_three_point_check_for_memory_leak(self, dataframe, node: str,
                                                   process: str, gain: float,
                                                   pid: str = None) -> bool:
        """Perform three point check

        Args:
         dataframe(panda dataframe): Panda dataframe of a given process
         node(str): Node on which memory leak has to be checked
         process(str): Name of process for which check has to be done
         gain(float): Accepted amount of leak for a given testcase in MB

        Optional:
         pid(str): pid of volume process for which 3 point check has to be done

        Returns:
         bool: True if memory leak instances are observed else False
        """
        # Filter dataframe to be process wise if it's volume specific process
        if process in ('glusterfs', 'glusterfsd'):
            if process == 'glusterfs' and pid:
                dataframe = dataframe[dataframe['Process ID'] == pid]

        # Compute usage gain throught the data frame
        memory_increments = list(dataframe['Memory Usage'].diff().dropna())

        # Check if usage is more than accepted amount of leak
        memory_leak_decision_array = np.where(
            dataframe['Memory Usage'].diff().dropna() > gain, True, False)
        instances_of_leak = np.where(memory_leak_decision_array)[0]

        # If memory leak instances are present check if it's reduced
        count_of_leak_instances = len(instances_of_leak)
        if count_of_leak_instances > 0:
            self.logger.error(f'There are {count_of_leak_instances} instances'
                              f' of memory leaks on node {node}')
            for instance in instances_of_leak:
                # In cases of last log file entry the below op could throw
                # IndexError which is handled as below.
                try:
                    # Check if memory gain had decrease in the consecutive
                    # entries, after 2 entry and betwen current and last entry
                    if all([memory_increments[instance+1]
                           > memory_increments[instance],
                           memory_increments[instance+2]
                           > memory_increments[instance],
                           (memory_increments[len(memory_increments)-1]
                            > memory_increments[instance])]):
                        return True

                except IndexError:
                    # In case of last log file entry rerun the command
                    # and check for difference
                    self.logger.info('Instance at last log entry.')
                    if process in ('glusterfs', 'glusterfsd'):
                        cmd = ("ps u -p %s | awk 'NR>1 && $11~/%s$/{print "
                               " $6/1024}'" % (pid, process))
                    else:
                        cmd = ("ps u -p `pgrep glusterd` | "
                               "awk 'NR>1 && $11~/glusterd$/{print $6/1024}'")
                    ret = self.execute_abstract_op_node(cmd, node)
                    if ret['error_code'] != 0:
                        self.logger.error('Unable to run the command to '
                                          'fetch current memory utilization.')
                        continue
                    usage_now = float(ret['msg'].replace('\n', '')[2])
                    last_entry = dataframe['Memory Usage'].iloc[-1]

                    # Check if current memory usage is higher than last entry
                    fresh_diff = last_entry - usage_now
                    if gain < fresh_diff < last_entry:
                        return True
        return False

    def check_for_memory_leaks_in_glusterd(self, nodes: list, test_name: str,
                                           gain: int = 30.0) -> bool:
        """Check for memory leaks in glusterd

        Args:
         nodes(list): Servers on which memory leaks have to be checked
         test_name(str): Name of testcase for which memory leaks has to be
                         checked
        Optional:
         gain(float): Accepted amount of leak for a given testcase in MB
                      (Default:30)

        Returns:
          bool: True if memory leak was obsevred else False
        """
        self.logger.debug("Checking for memory leak in glusterd")
        is_there_a_leak = []
        for node in nodes:
            dataframe = self.create_dataframe_from_csv(node, 'glusterd',
                                                       test_name)
            if dataframe.empty:
                self.logger.error("Dataframe is Empty")
                return False

            # Call 3 point check function
            check = (self._perform_three_point_check_for_memory_leak(
                     dataframe, node, 'glusterd', gain))
            if check:
                self.logger.error(f"Memory leak observed on node {node} in "
                                  "glusterd")
            is_there_a_leak.append(check)

        return any(is_there_a_leak)

    def check_for_memory_leaks_in_glusterfs(self, nodes: list, test_name: str,
                                            vol_name: str,
                                            gain: int = 30.0) -> bool:
        """Check for memory leaks in glusterfs

        Args:
         nodes(list): Servers on which memory leaks have to be checked
         test_name(str): Name of testcase for which memory leaks has to be
                         checked
         vol_name(str): Name of volume process according to volume status
        Optional:
         gain(float): Accepted amount of leak for a given testcase in MB
                      (Default:30)

        Returns:
          bool: True if memory leak was obsevred else False

        NOTE:
         This function should be executed with the volumes present on the
         cluster
        """
        self.logger.debug("Checking for memory leak in glusterfs")
        is_there_a_leak = []
        for node in nodes:
            # Get the volume status on the node
            volume_status = self.get_volume_status(vol_name, node)
            if volume_status is None:
                self.logger.error("Failed to get volume status")
                return False
            dataframe = self.create_dataframe_from_csv(node, 'glusterfs',
                                                       test_name)
            if dataframe.empty:
                self.logger.error("Dataframe is Empty")
                return False

            for volume in volume_status:
                for process in volume_status[vol_name]['node']:
                    # Skiping if process isn't Self-heal Deamon
                    if process['hostname'] != 'Self-heal Daemon':
                        continue

                    # Call 3 point check function
                    pid = process['pid']
                    check = (self._perform_three_point_check_for_memory_leak(
                             dataframe, node, 'glusterfs', gain, pid))
                    if check:
                        self.logger.error("Memory leak observed on node "
                                          f"{node} in shd on volume "
                                          f"{volume}")
                    is_there_a_leak.append(check)

        return any(is_there_a_leak)

    def check_for_memory_leaks_in_glusterfsd(self, nodes: list,
                                             test_name: str, vol_name: str,
                                             gain: int = 30.0) -> bool:
        """Check for memory leaks in glusterfsd

        Args:
         nodes(list): Servers on which memory leaks have to be checked
         test_name(str): Name of testcase for which memory leaks has to be
                         checked
         vol_name(str): Name of volume process according to volume status
        Optional:
         gain(float): Accepted amount of leak for a given testcase in MB
                      (Default:30)
        Returns:
          bool: True if memory leak was obsevred else False

        NOTE:
         This function should be executed with the volumes present on the
         cluster.
        """
        self.logger.debug("Checking for memory leak in glusterfsd")
        is_there_a_leak = []
        for node in nodes:
            # Get the volume status on the node
            volume_status = self.get_volume_status(vol_name, node)
            if volume_status is None:
                self.logger.error("Failed to get volume status")
                return False
            dataframe = self.create_dataframe_from_csv(node, 'glusterfsd',
                                                       test_name)
            if dataframe.empty:
                self.logger.error("Dataframe is Empty")
                return False

            for volume in volume_status:
                for process in volume_status[vol_name]['node']:
                    # Skiping if process isn't brick process
                    if not process['path'].count('/'):
                        continue

                    # Call 3 point check function
                    pid = process['pid']
                    check = (self._perform_three_point_check_for_memory_leak(
                             dataframe, node, 'glusterfsd', gain, pid))
                    if check:
                        self.logger.error("Memory leak observed on node "
                                          f"{node} in brick process for "
                                          f"brick {process} on volume "
                                          f"{volume}")
                    is_there_a_leak.append(check)

        return any(is_there_a_leak)

    def check_for_memory_leaks_and_oom_kills_on_servers(self, test_id: str,
                                                        nodes: list,
                                                        vol_name: str,
                                                        gain=30.0) -> bool:
        """Check for memory leaks and OOM kills on servers

        Args:
         test_id(str): ID of the test running fetched from self.id()
         nodes(list): Servers on which memory leaks have to be checked
         vol_name(str): Name of volume process according to volume status
        Optional:
         gain(float): Accepted amount of leak for a given testcase in MB
                      (Default:30)

        Returns:
         bool: True if memory leaks or OOM kills are observed else false
        """
        # Check for memory leaks on glusterd
        if self.check_for_memory_leaks_in_glusterd(nodes, test_id,
                                                   gain):
            self.logger.error("Memory leak on glusterd.")
            return True

        volume_type_info = self.get_volume_type_info(nodes[0], vol_name)
        if volume_type_info is None:
            self.logger.error("Failed to get volume type info")
            return None
        volume_type = volume_type_info['volume_type_info']['typeStr']
        if volume_type != 'Distribute':
            # Check for memory leaks on shd
            if self.check_for_memory_leaks_in_glusterfs(nodes, test_id,
                                                        vol_name, gain):
                self.logger.error("Memory leak on shd.")
                return True

        # Check for memory leaks on brick processes
        if self.check_for_memory_leaks_in_glusterfsd(nodes, test_id,
                                                     vol_name, gain):
            self.logger.error("Memory leak on brick process.")
            return True

        # Check OOM kills on servers for all gluster server processes
        if self.check_for_oom_killers_on_servers(nodes):
            self.logger.error('OOM kills present on servers.')
            return True
        return False

    def check_for_memory_leaks_in_glusterfs_fuse(self, nodes: list,
                                                 test_name: str,
                                                 gain: int = 30.0):
        """Check for memory leaks in glusterfs fuse

        Args:
         nodes(list): Servers on which memory leaks have to be checked
         test_name(str): Name of testcase for which memory leaks has to be
                         checked

        Optional:
         gain(float): Accepted amount of leak for a given testcase in MB
                      (Default:30)

        Returns:
          bool: True if memory leak was observed else False

        NOTE:
         This function should be executed when the volume is still mounted.
        """
        self.logger.debug("Checking for memory leak in glusterfs_fuse")
        is_there_a_leak = []
        for node in nodes:
            # Get the volume status on the node
            dataframe = self.create_dataframe_from_csv(node, 'glusterfs',
                                                       test_name)
            if dataframe.empty:
                self.logger.error("Dataframe is Empty")
                return False

            # Call 3 point check function
            check = (self._perform_three_point_check_for_memory_leak(
                     dataframe, node, 'glusterfs', gain))
            if check:
                self.logger.error(f"Memory leak observed on node {node} for"
                                  " client")

                # If I/O is constantly running on Clients the memory
                # usage spikes up and stays at a point for long.
                last_entry = dataframe['Memory Usage'].iloc[-1]
                cmd = ("ps u -p `pidof glusterfs` | "
                       "awk 'NR>1 && $11~/glusterfs$/{print"
                       " $6/1024}'")
                ret = self.execute_abstract_op_node(cmd, node)
                if ret['error_code'] != 0:
                    self.logger.error('Unable to run the command to fetch '
                                      'current memory utilization.')
                    continue

                out = ret['msg']
                if float(out) != last_entry:
                    if float(out) > last_entry:
                        is_there_a_leak.append(True)
                        continue

            is_there_a_leak.append(False)

        return any(is_there_a_leak)

    def check_for_memory_leaks_and_oom_kills_on_clients(self, test_id: str,
                                                        nodes: list,
                                                        gain=30) -> bool:
        """Check for memory leaks and OOM kills on clients

        Args:
         test_id(str): ID of the test running fetched from self.id()
         nodes(list): Servers on which memory leaks have to be checked
        Optional:
         gain(float): Accepted amount of leak for a given testcase in MB
                      (Default:30)

        Returns:
         bool: True if memory leaks or OOM kills are observed else false
        """
        # Check for memory leak on glusterfs fuse process
        if self.check_for_memory_leaks_in_glusterfs_fuse(nodes,
                                                         test_id, gain):
            self.logger.error("Memory leaks observed on FUSE clients.")
            return True

        # Check for oom kills on clients
        if self.check_for_oom_killers_on_clients(nodes):
            self.logger.error("OOM kills present on clients.")
            return True
        return False
