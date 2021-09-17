"""
Copyright (C) 2020 Red Hat, Inc. <http://www.redhat.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along`
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-131 USA.

Description: Test to check no errors on file/dir renames when one of
                        the bricks is down in the volume.
"""

from random import choice
from time import sleep
from tests.d_parent_test import DParentTest

# disruptive;disp,dist-disp


class TestECRenameFilesOnBrickDown(DParentTest):
    @DParentTest.setup_custom_enable
    def setup_test(self):
        # Check server requirements
        self.redant.check_hardware_requirements(clients=self.client_list,
                                                clients_count=2)

        # Create and start the volume
        conf_hash = self.vol_type_inf[self.volume_type]
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots, force=True)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node("mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            self.redant.volume_mount(self.server_list[0], self.vol_name,
                                     self.mountpoint, client)

    def create_links(self, client, path):
        # Soft links
        for i in range(4, 7):
            if not (self.redant.
                    create_link_file(client, f'{path}/file{i}_or',
                                     f'{path}/file{i}_sl',
                                     soft=True)):
                raise Exception("Unable to create soft link file.")

        # Hard links
        for i in range(7, 10):
            if not (self.redant.
                    create_link_file(client, f'{path}/file{i}_or',
                                     f'{path}/file{i}_hl')):
                raise Exception("Unable to create hard link file.")

    def run_test(self, redant):
        """
        Steps:
        1. Create an EC volume
        2. Mount the volume using FUSE on two different clients
        3. Create ~9 files from one of the client
        4. Create ~9 dir with ~9 files each from another client
        5. Create soft-links, hard-links for file{4..6}, file{7..9}
        6. Create soft-links for dir{4..6}
        7. Begin renaming the files, in multiple iterations
        8. Bring down a brick while renaming the files
        9. Bring the brick online after renaming some of the files
        10. Wait for renaming of the files
        11. Validate no data loss and files are renamed successfully
        """

        # Creating ~9 files from client 1 on mount
        cmd = 'cd %s; touch file{1..9}_or' % self.mountpoint
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Creating 9 dir X 9 files in each dir from client 2
        cmd = ('cd %s; mkdir -p dir{1..9}_or;'
               'touch dir{1..9}_or/file{1..9}_or' % self.mountpoint)
        redant.execute_abstract_op_node(cmd, self.client_list[1])

        # Create required soft links and hard links from client 1 on mount
        self.create_links(self.client_list[0], self.mountpoint)

        # Create required soft and hard links in nested dirs from client2
        for i in range(1, 10):
            path = (f'{self.mountpoint}/dir{i}_or')
            self.create_links(self.client_list[1], path)

        # Create soft links for dirs from client2
        path = self.mountpoint
        for i in range(4, 7):
            if not (self.redant.
                    create_link_file(self.client_list[1], f'{path}/dir{i}_or',
                                     f'{path}/dir{i}_sl', soft=True)):
                raise Exception("Unable to create soft link file for dir")

        # Calculate all file count against each section orginal, hard, soft
        # links
        cmd = (f'cd {path}; arr=(or sl hl); '
               'for i in ${arr[*]}; do find . -name "*$i" | wc -l ; done;')
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])
        count = []
        for i in ret['msg']:
            count.append(int(i.strip()))
        all_org, all_soft, all_hard = count

        # Rename 2 out of 3 dir's soft links from client 1
        cmd = (f'cd {path}; sl=0; '
               'for line in `ls -R | grep -P "dir(4|5)_sl"`; '
               'do mv -f "$line" "$line""_renamed"; ((sl++)); done; '
               'echo $sl;')
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])
        temp_soft = int(ret['msg'][0].strip())

        # Start renaming original files from client 1 and
        # softlinks, hardlinks  from client 2
        cmd = (f'cd {path}; '
               'arr=(. dir{1..9}_or);  or=0; '
               'for item in ${arr[*]}; do cd $item; '
               'for line in `ls | grep -P "file(1|2)_or"`; '
               'do mv -f "$line" "$line""_renamed"; ((or++)); '
               'sleep 2; done;''cd - > /dev/null; sleep 1; done; echo $or ')
        proc_or = redant.execute_command_async(cmd, self.client_list[0])

        cmd = (f'cd {path}; '
               'arr=(. dir{1..9}_or); sl=0; hl=0; '
               'for item in ${arr[*]}; do cd $item; '
               'for line in `ls | grep -P "file(4|5)_sl"`; '
               'do mv -f "$line" "$line""_renamed"; ((sl++)); '
               'sleep 1; done; '
               'for line in `ls | grep -P "file(7|8)_hl"`; '
               'do mv -f "$line" "$line""_renamed"; ((hl++)); '
               'sleep 1; done; '
               'cd - > /dev/null; sleep 1; done; echo $sl $hl; ')
        proc_sl_hl = redant.execute_command_async(cmd, self.client_list[1])

        # Wait for some files to be renamed
        sleep(20)

        # Kill one of the bricks
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        bricks_offline = choice(bricks_list)
        redant.bring_bricks_offline(self.vol_name, bricks_offline)
        if not redant.are_bricks_offline(self.vol_name, bricks_offline,
                                         self.server_list[0]):
            raise Exception(f"Brick {bricks_offline} is not offline")

        # Wait for some more files to be renamed
        sleep(20)

        # Bring brick online
        redant.volume_start(self.vol_name, self.server_list[0],
                            force=True)

        # Wait for rename to complete and take count of file operations
        ret1 = redant.wait_till_async_command_ends(proc_or)
        ret2 = redant.wait_till_async_command_ends(proc_sl_hl)

        ren_org = int(ret1['msg'][0].strip())
        ren_soft, ren_hard = ret2['msg'][0].strip().split()
        ren_soft = str(int(ren_soft) + int(temp_soft))

        # Count actual data of renaming links/files
        cmd = (f'cd {path}; arr=(or or_renamed sl sl_renamed hl hl_renamed); '
               'for i in ${arr[*]}; do find . -name "*$i" | wc -l ; done;')
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])
        count = []
        for i in ret['msg']:
            count.append(int(i.strip()))

        (act_org, act_org_ren, act_soft,
         act_soft_ren, act_hard, act_hard_ren) = count

        # Validate count of expected and actual rename of
        # links/files is matching
        for exp, act, msg in (
                (int(ren_org), int(act_org_ren), 'original'),
                (int(ren_soft), int(act_soft_ren), 'soft links'),
                (int(ren_hard), int(act_hard_ren), 'hard links')):
            if exp != act:
                raise Exception(f"Count of {msg} files renamed while brick "
                                "was offline is not matching")
        # Validate no data is lost in rename process
        for exp, act, msg in (
                (int(all_org)-int(act_org_ren), int(act_org), 'original'),
                (int(all_soft)-int(act_soft_ren), int(act_soft), 'soft links'),
                (int(all_hard)-int(act_hard_ren), int(act_hard), 'hard links'),
        ):
            if exp != act:
                raise Exception(f"Count of {msg} files which are not "
                                "renamed while brick was offline "
                                "is not matching")
