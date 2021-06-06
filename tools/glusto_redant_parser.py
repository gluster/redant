import re
import argparse
import copy
from os import path


def get_brc_data(line: str, brc_dict: dict, append_flag: bool) -> dict:
    """
    Count the occurences of parenthesis, braces and bracket components
    in the provided lines and accordingly update the brc_dict
    Args:
        line (str)
        brc_dict (dict) : Dictionary containing the count of the said values.
        append_flag (bool) : Indicating whether the dictionary has to be
                             re-created.
    """
    delimiting_char_list = ["{", "}", "[", "]", "(", ")"]
    if not append_flag:
        for val in delimiting_char_list:
            brc_dict[val] = 0

    for val in delimiting_char_list:
        val_count = line.count(val)
        brc_dict[val] += val_count

    return brc_dict


def brc_finish_check(brc_dict: dict) -> bool:
    """
    To check if the matching brackets, parenthesis and braces are
    reached or not.
    """
    if brc_dict["{"] != brc_dict["}"]:
        return False
    if brc_dict["["] != brc_dict["]"]:
        return False
    if brc_dict["("] != brc_dict[")"]:
        return False
    return True


def multi_to_single_line(glusto_tc_ml_lines: list) -> list:
    """
    For regex to work properly, the parenthesis, brackets and braces
    should be accounted for and hence expressions should exist on a single
    line. this is contrary to how python strictly says but then again, we
    are parsing an existing code to modify it to our taste, hence the user
    can handle the lint issues later.
    Arg:
        glusto_tc_ml_lines (list) : List of lines from the glusto test case
                                    which was read. Now certain expressions,
                                    function calls, import statements etc
                                    go for multiple lines and exist in
                                    different lines in this var.
    Returns:
        list: Expressions, function calls and import statements spanning
              multiple lines are now in one single line.
    """
    brc_dict_val = {}
    itr = 0
    optimized_code = []
    append_flag = False
    mainline = ""
    tot_lines = len(glusto_tc_ml_lines)
    while itr < tot_lines:
        if not append_flag:
            brc_dict_val = {}
        brc_dict_val = get_brc_data(
            glusto_tc_ml_lines[itr], brc_dict_val, append_flag)
        if append_flag:
            line_value = glusto_tc_ml_lines[itr].lstrip()
            mainline = (f"{mainline}{line_value}")
        else:
            mainline = (f"{glusto_tc_ml_lines[itr]}")
        if brc_finish_check(brc_dict_val):
            optimized_code.append(mainline)
            append_flag = False
        else:
            append_flag = True
        itr += 1

    return optimized_code


def parse_segments(glusto_tc_lines: list) -> dict:
    """
    Parsing the glusto code lines to divide it into said segments. For more
    more information, please refer the migrate_code.md in the docs.
    """
    glusto_segs = {"licenseL": [], "docstringL": [], "importL": [],
                   "runsOnL": []}

    import_lines_re = re.compile('^import .+')
    from_import_g_re = re.compile('^from glusto.+')
    from_import_ng_re = re.compile('^from [^g].+')
    runs_on_re = re.compile('^@runs')

    for line in glusto_tc_lines[:15]:
        glusto_segs["licenseL"].append(line)

    for line in glusto_tc_lines[15:]:
        if import_lines_re.match(line) is not None:
            glusto_segs["importL"].append(line)
            continue
        if from_import_g_re.match(line) is not None:
            continue
        if from_import_ng_re.match(line) is not None:
            glusto_segs["importL"].append(line)
            continue
        if runs_on_re.match(line) is not None:
            glusto_segs["runsOnL"].append(line)
            continue

    return glusto_segs


def convert_license(license_list: list) -> list:
    """
    Convert the Glusto-tests test case license structure into
    Redant license structure.
    Arg:
        license_list (list)
    Returns:
        list
    """
    converted_lic_list = []
    for line in license_list:
        if line == "#":
            line = ""
        converted_lic_list.append(line[3:])
    return converted_lic_list


def obtain_tc_nature(runs_on_list: list) -> str:
    """
    Converts the runs on line into a redant specific
    comment in a test case which would be used for
    identifying and deciding the behavior of the said
    test case during execution.
    """
    gr_vol_mapping = {"distributed": "dist", "replicated": "rep",
                      "distributed-replicated": "dist-rep",
                      "arbiter": "arb", "dispersed": "disp",
                      "distributed-arbiter": "dist-arb",
                      "distributed-dispersed": "dist-disp"}
    if runs_on_list == []:
        return ["#"]
    vol_list = \
        runs_on_list[0][11:runs_on_list[0].find(
            ']', 9)].replace("'", "").split(',')
    vol_list = [gr_vol_mapping[vol_data.strip()] for vol_data in vol_list]
    return "#;"+",".join(vol_list)


def modify_class_seg(class_lines: list) -> list:
    """
    Modify the class segment by removing the components specific to glusto.
    """
    def_re = re.compile('^def')
    setup_re = re.compile('^def setUp.+')
    tear_re = re.compile('^def tearDown.+')
    assert_re = re.compile('^self\.assert.+')
    glog_re = re.compile('^g\.log\..+')

    modified_class_lines = []
    itr = 0
    ignore_flag = False
    while itr < len(class_lines):
        temp_line = copy.deepcopy(class_lines[itr].lstrip())
        if def_re.match(temp_line) is not None:
            if ignore_flag:
                ignore_flag = False
            if setup_re.match(temp_line) is not None or \
                    tear_re.match(temp_line) is not None:
                ignore_flag = True
        if ignore_flag or assert_re.match(temp_line) is not None or \
                glog_re.match(temp_line) is not None:
            itr += 1
            continue
        modified_class_lines.append(class_lines[itr])
        itr += 1
    return modified_class_lines


def parse_args():
    """
    Function to create a command line parser
    """
    parser = argparse.ArgumentParser(
        description='Glusto to redant test conversion script'
    )
    parser.add_argument("-tpath", "--tc_pat", dest="tp", type=str,
                        default=None, required=True,
                        help="path of test case file.")
    return parser.parse_args()


def main():
    """
    Added for the happiness of the linter :/
    """
    args = parse_args()
    args.tp = path.abspath(args.tp)
    tc_fd = open(args.tp, "r")
    glusto_tc_raw_lines = tc_fd.readlines()
    tc_fd.close()

    # Stip the endline.
    glusto_tc_lines = []
    for line in glusto_tc_raw_lines:
        line_value = line.strip("\n")
        # if line_value == '':
        #    continue
        glusto_tc_lines.append(line_value)
    del glusto_tc_raw_lines

    # Converting multiline to single line.
    glusto_tc_lines = multi_to_single_line(glusto_tc_lines)

    # Separate the class segment from other segments.
    class_re = re.compile('^class Test.+')
    class_segment = []
    initial_segment = []
    itr = 0
    while True:
        line = glusto_tc_lines[itr]
        if class_re.match(line) is None:
            itr += 1
            continue
        class_segment = glusto_tc_lines[itr:]
        initial_segment = glusto_tc_lines[:itr]
        break

    # Get glusto segments.
    glusto_initial_seg = parse_segments(initial_segment)

    # Conversions from glusto to redant.
    redant_initial_seg = {"licenseL": [], "importL": [], "tcNatureL": ""}
    redant_initial_seg["licenseL"] = convert_license(
        glusto_initial_seg["licenseL"])
    redant_initial_seg["importL"] = glusto_initial_seg["importL"]
    redant_initial_seg["tcNatureL"] = obtain_tc_nature(
        glusto_initial_seg["runsOnL"])

    # Identifying the class parameters and modifying them.
    # Basically removing anything setup, teardown
    redant_class_seg = modify_class_seg(class_segment)

    # Truncate the test file
    tc_fd = open(args.tp, "w")
    tc_fd.truncate()

    # Add the license segment.
    tc_fd.write('"""\n')
    tc_fd.write('\n'.join(redant_initial_seg["licenseL"])+'\n')
    tc_fd.write('"""\n')

    # Add the import lines.
    tc_fd.write('\n')
    tc_fd.write('\n'.join(redant_initial_seg["importL"])+'\n')
    tc_fd.write("from tests._parent_test import ParentTest")
    tc_fd.write('\n\n')

    # Add the test case nature
    tc_fd.write(redant_initial_seg["tcNatureL"])
    tc_fd.write('\n\n')

    # Add the class
    tc_fd.writelines('\n'.join(redant_class_seg)+'\n')
    tc_fd.close()


if __name__ == "__main__":
    main()
