"""
This component handles the
results in two ways:

1. display on the CLI
2. store in a file
"""
from os import stat
from colorama import Fore, Style
import xlwt
import copy
from xlwt import Workbook
from prettytable import PrettyTable


class ResultHandler:

    @classmethod
    def _sanitize_time_format(cls, data: int) -> str:
        """
        The function formats the values to 0X or XY
        format.

        Args:
            data (int): The time data.
        Returns:
            str
        """
        if len(str(data)) != 2:
            return f"0{data}"
        return f"{data}"

    @classmethod
    def _time_rollover_conversion(cls, time_in_sec: float,
                                  expanded_f: bool = False) -> str:
        """
        The function takes in input in raw seconds and converts
        it to the format of x HH:MM:SS, wherein the x can be
        replaced by `y days` if there is a rollover till days.

        Args:
            time_in_sec (float): as name suggests time run in seconds.
            expanded_f (bool): By default False. This converts the result
                               into an expanded form of,
                               w days x hours y minutes z seconds.
        Returns:
            str in the form of HH:MM:SS or y days HH:MM:SS or in the form of
            w days x hours y minutes z seconds in expanded form.
        """
        days = 0
        hours = 0
        minutes = 0
        seconds = 0

        time_in_sec = int(time_in_sec)
        if time_in_sec >= 60:
            seconds = time_in_sec % 60
            time_in_sec -= seconds
            time_in_min = int(time_in_sec / 60)
            if time_in_min >= 60:
                minutes = time_in_min % 60
                time_in_min -= minutes
                time_in_hour = int(time_in_min / 60)
                if time_in_hour >= 24:
                    hours = time_in_hour % 24
                    time_in_hour -= hours
                    days = int(time_in_hour / 24)
                else:
                    hours = int(time_in_hour)
            else:
                minutes = int(time_in_min)
        else:
            seconds = time_in_sec

        seconds = cls._sanitize_time_format(seconds)
        minutes = cls._sanitize_time_format(minutes)
        hours = cls._sanitize_time_format(hours)

        if days != 0:
            if not expanded_f:
                return f"{days} days {hours}:{minutes}:{seconds}"
            else:
                return (f"{days} days {hours} hours {minutes} minutes"
                        f" {seconds} seconds")
        if not expanded_f:
            return f"{hours}:{minutes}:{seconds}"
        return f"{hours} hours {minutes} minutes {seconds} seconds"

    @classmethod
    def _get_output(cls, test_results: dict, colorify: bool,
                    total_time: float):
        """
        It generates the output in the
        form of tables with columns
        containing volume type, test result
        and the time taken to execute the test

        Args:
        test_results: All the tests result.
        colorify: Stores whether to show colored
                output or not
        total_time: stores the total time taken by the framework

        """
        cls.result = "Table:\n"
        dcount = 0
        ndcount = 0
        dpass = 0
        ndpass = 0
        dtest = 0
        ndtest = 0
        skipCount = 0

        for item in test_results:
            if colorify:
                cls.result = (f"{cls.result} {Fore.BLUE}{item}\n")
                cls.result = (f"{cls.result} {Style.RESET_ALL}\n")
            else:
                cls.result = (f"{cls.result} {item}\n")

            table = PrettyTable(
                ['Volume Type', 'Test Result', 'Time taken (HH:MM:SS)',
                 'Skip Reason'])

            if test_results[item][0]['tcNature'] == 'disruptive' and\
                    test_results[item][0]['testResult'] is not None:
                dtest += 1
            elif test_results[item][0]['tcNature'] == 'nonDisruptive' and\
                    test_results[item][0]['testResult'] is not None:
                ndtest += 1
            else:
                print(item)
                skipCount += 1

            for each_vol_test in test_results[item]:

                if each_vol_test['testResult'] is not None:
                    skip_reason = "N/A"
                    if each_vol_test['tcNature'] == 'disruptive':
                        dcount += 1
                        if each_vol_test['testResult'] == 'PASS':
                            dpass += 1
                    elif each_vol_test['tcNature'] == 'nonDisruptive':
                        ndcount += 1
                        if each_vol_test['testResult'] == 'PASS':
                            ndpass += 1
                elif each_vol_test['testResult'] is None:
                    skip_reason = each_vol_test['skipReason']

                time_taken = cls._time_rollover_conversion(
                    each_vol_test['timeTaken'])
                table.add_row(
                    [each_vol_test['volType'], each_vol_test['testResult'],
                     time_taken, skip_reason])

            cls.result = (f"{cls.result}{str(table)}\n\n")

        table = PrettyTable(['Category',
                             'Cases',
                             'Pass Percent'])

        table.add_row(['nonDisruptive', ndtest,
                       0 if ndcount == 0 else (ndpass/ndcount)*100])
        table.add_row(['Disruptive', dtest,
                       0 if dcount == 0 else (dpass/dcount)*100])
        table.add_row(['Skipped', skipCount, 0])
        table.add_row(['Total', ndtest+dtest,
                       (0 if (ndcount + dcount == 0)
                        else ((ndpass + dpass)/(ndcount + dcount))*100)])

        cls.result = (f"Summary:\n{str(table)}\n{cls.result}\n")

        time_taken = cls._time_rollover_conversion(total_time, True)
        cls.result = (f"{cls.result}\nFramework runtime : {time_taken}\n")

    @classmethod
    def _display_test_results(cls, test_results: dict, total_time: float):
        """
        This function displays the test results
        in the form of tables.

        Args:
        test_results: All the tests results.
        total_time: stores the total time taken by the framework

        """
        cls._get_output(test_results, True, total_time)
        print(cls.result)

    @classmethod
    def _store_results(cls, test_results: dict, result_path: str,
                       total_time: float):
        """
        This function stores the test results
        in the form of tables in a file.

        Args:
        test_results: All the tests results.
        result_path: Path of the result file
        total_time: stores the total time taken by the framework
        """
        cls._get_output(test_results, False, total_time)
        print(f"The results are stored in {result_path}")
        file = open(result_path, 'w')
        file.write(cls.result)
        file.close()

    @classmethod
    def store_results_in_excelsheet(cls, excel_sheet: str, test_results: dict,
                                    total_time: float):
        """
        This method stores the
        results of the test(s) run
        in an excel sheet for better understanding.

        Args:
        excel_sheet: stores the path of excel sheet
        test_results: stores the test results
        total_time: total time taken by the framework
        """
        wb = Workbook()

        result_sheet = wb.add_sheet('Result Sheet')

        dcount = 0
        ndcount = 0
        dpass = 0
        ndpass = 0
        dtest = 0
        ndtest = 0
        skipCount = 0

        for item in test_results:
            if test_results[item][0]['tcNature'] == 'disruptive' and\
                    test_results[item][0]['testResult'] is not None:
                dtest += 1
            elif test_results[item][0]['tcNature'] == 'nonDisruptive' and\
                    test_results[item][0]['testResult'] is not None:
                ndtest += 1
            else:
                skipCount += 1

            for each_vol_test in test_results[item]:

                if each_vol_test['testResult'] is not None:
                    if each_vol_test['tcNature'] == 'disruptive':
                        dcount += 1
                        if each_vol_test['testResult'] == 'PASS':
                            dpass += 1
                    elif each_vol_test['tcNature'] == 'nonDisruptive':
                        ndcount += 1
                        if each_vol_test['testResult'] == 'PASS':
                            ndpass += 1

        row = 0
        style = xlwt.easyxf('font: bold 1')

        result_sheet.write(row, 0, 'Category', style)
        result_sheet.write(row, 1, 'Cases', style)
        result_sheet.write(row, 2, 'Pass Percent', style)

        row += 1
        result_sheet.write(row, 0, 'nonDisruptive')
        result_sheet.write(row, 1, ndtest)
        result_sheet.write(row, 2,
                           0 if ndcount == 0
                           else (ndpass/ndcount)*100)

        row += 1
        result_sheet.write(row, 0, 'Disruptive')
        result_sheet.write(row, 1, dtest)
        result_sheet.write(row, 2,
                           0 if dcount == 0
                           else (dpass/dcount)*100)

        row += 1
        result_sheet.write(row, 0, 'Skipped')
        result_sheet.write(row, 1, skipCount)
        result_sheet.write(row, 2, 0)

        row += 1
        result_sheet.write(row, 0, 'Total')
        result_sheet.write(row, 1, ndtest + dtest)
        result_sheet.write(row, 2,
                           (0 if (ndcount + dcount == 0)
                            else
                            ((ndpass + dpass)/(ndcount + dcount))*100))

        row += 2

        result_sheet.write(row, 0, 'Total time taken (HH:MM:SS)', style)
        time_taken = cls._time_rollover_conversion(total_time, True)
        result_sheet.write(row, 1, time_taken)
        row += 2

        for item in test_results:
            result_sheet.write(row, 0, item, style)
            row += 1
            result_sheet.write(row, 0, 'Volume Type', style)
            result_sheet.write(row, 1, 'Test Result', style)
            result_sheet.write(row, 2, 'Time Taken (HH:MM:SS)', style)
            result_sheet.write(row, 3, 'Skip Reason', style)
            row += 1

            for each_vol_test in test_results[item]:
                result_sheet.write(row, 0, each_vol_test['volType'])
                result_sheet.write(row, 1, each_vol_test['testResult'])
                time_taken = cls._time_rollover_conversion(
                    each_vol_test['timeTaken'])
                result_sheet.write(row, 2, time_taken)
                if each_vol_test['testResult'] is None:
                    skip_reason = str(each_vol_test['skipReason'])
                else:
                    skip_reason = "NA"
                result_sheet.write(row, 3, skip_reason)
                row += 1

            row += 2

        wb.save(excel_sheet)

def _sanitize_time_format(data: int) -> str:
    """
    The function formats the values to 0X or XY
    format.

    Args:
        data (int): The time data.
    Returns:
        str
    """
    if len(str(data)) != 2:
        return f"0{data}"
    return f"{data}"

def _time_rollover_conversion(time_in_sec: float,
                              expanded_f: bool = False) -> str:
    """
    The function takes in input in raw seconds and converts
    it to the format of x HH:MM:SS, wherein the x can be
    replaced by `y days` if there is a rollover till days.

    Args:
        time_in_sec (float): as name suggests time run in seconds.
        expanded_f (bool): By default False. This converts the result
                           into an expanded form of,
                           w days x hours y minutes z seconds.
    Returns:
        str in the form of HH:MM:SS or y days HH:MM:SS or in the form of
        w days x hours y minutes z seconds in expanded form.
    """
    days = 0
    hours = 0
    minutes = 0
    seconds = 0

    time_in_sec = int(time_in_sec)
    if time_in_sec >= 60:
        seconds = time_in_sec % 60
        time_in_sec -= seconds
        time_in_min = int(time_in_sec / 60)
        if time_in_min >= 60:
            minutes = time_in_min % 60
            time_in_min -= minutes
            time_in_hour = int(time_in_min / 60)
            if time_in_hour >= 24:
                hours = time_in_hour % 24
                time_in_hour -= hours
                days = int(time_in_hour / 24)
            else:
                hours = int(time_in_hour)
        else:
            minutes = int(time_in_min)
    else:
        seconds = time_in_sec

    seconds = _sanitize_time_format(seconds)
    minutes = _sanitize_time_format(minutes)
    hours = _sanitize_time_format(hours)

    if days != 0:
        if not expanded_f:
            return f"{days} days {hours}:{minutes}:{seconds}"
        else:
            return (f"{days} days {hours} hours {minutes} minutes"
                    f" {seconds} seconds")
    if not expanded_f:
        return f"{hours}:{minutes}:{seconds}"
    return f"{hours} hours {minutes} minutes {seconds} seconds"

def _transform_queue_to_dict(resultQueue) -> dict:
    """
    Function to transform the queue to a dictionary.

    Args:
        resultQueue: It is a queue containing the test run results.

    Returns:
        A dictionary with classification of tests based on,
        1. Component,
        2. Test Nature,
        3. Test Name
    """
    testResults = {}
    while not resultQueue.empty():
        testDict = resultQueue.get()
        tName = list(testDict.keys())[0]
        component = testDict[tName]['component']
        tcNature = testDict[tName]['tcNature']
        tVolT = testDict[tName]['volType']
        if tcNature == 's':
            component = "Special"
            tcNature = "nonDisruptive"
        if component not in testResults.keys():
            testResults[component] = {}
        if tcNature not in testResults[component].keys():
            testResults[component][tcNature] = {}
        if tName not in testResults[component][tcNature].keys():
            testResults[component][tcNature][tName] = {}
        tempDict = {}
        tempDict['testResult'] = testDict[tName]['testResult']
        tempDict['timeTaken'] = testDict[tName]['timeTaken']
        testResults[component][tcNature][tName][tVolT] = copy.deepcopy(
            tempDict)
    return testResults

def _obtain_stat(resultDict: dict) -> dict:
    """
    Function to obtain the statistics
    about the test runs.

    Args:
        stattDict (dict): Dictionary containing the stat.
    """
    statDict = {}

    # Create component keys inside the statDict
    for component in resultDict.keys():
        statDict[component] = {}

    # Get component-wise data.
    for component in resultDict:
        dCount = 0
        ndCount = 0
        dSkipCount = 0
        ndSkipCount = 0
        dPass = 0
        ndPass = 0

        crDict = resultDict[component]
        # First step is to get the disruptive tests provided
        # they exist in this component, followed by non-disruptive.
        # Once that is done, we can simply aggregate them for
        # total count.
        if "disruptive" in crDict.keys():
            disCrDict = crDict['disruptive']
            dCount += len(list(disCrDict.keys()))
            for test in disCrDict:
                for volT in disCrDict[test]:
                    if disCrDict[test][volT]['testResult'] == "PASS":
                        dPass += 1
                    elif disCrDict[test][volT]['testResult'] == "SKIP":
                        dSkipCount += 1
        elif "nonDisruptive" in crDict.keys():
            ndisCrDict = crDict['nonDisruptive']
            ndCount += len(list(ndisCrDict.keys()))
            for test in ndisCrDict:
                for volT in ndisCrDict[test]:
                    if ndisCrDict[test][volT]['testResult'] == "PASS":
                        ndPass += 1
                    elif ndisCrDict[test][volT]['testResult'] == "SKIP":
                        ndSkipCount += 1

        tempDict = {}
        tempDict['dCount'] = dCount
        tempDict['ndCount'] = ndCount
        tempDict['totalCount'] = dCount + ndCount
        tempDict['dSkipCount'] = dSkipCount
        tempDict['ndSkipCount'] = ndSkipCount
        tempDict['skipCount'] = dSkipCount + ndSkipCount
        tempDict['runCount'] = tempDict['totalCount'] - tempDict['skipCount']
        tempDict['dPass'] = dPass
        tempDict['ndPass'] = ndPass
        tempDict['Pass'] = dPass + ndPass
        statDict[component] = copy.deepcopy(tempDict)

    # Aggregating the component results in Total component.
    statDict['Total'] = {}
    statDict['Total']['dCount'] = 0
    statDict['Total']['ndCount'] = 0
    statDict['Total']['dSkipCount'] = 0
    statDict['Total']['ndSkipCount'] = 0
    statDict['Total']['dPass'] = 0
    statDict['Total']['ndPass'] = 0
    for component in statDict:
        if component == 'Total':
            continue
        statDict['Total']['dCount'] += statDict[component]['dCount']
        statDict['Total']['ndCount'] += statDict[component]['ndCount']
        statDict['Total']['dSkipCount'] += statDict[component]['dSkipCount']
        statDict['Total']['ndSkipCount'] += statDict[component]['ndSkipCount']
        statDict['Total']['dPass'] += statDict[component]['dPass']
        statDict['Total']['ndPass'] += statDict[component]['ndPass']
    statDict['Total']['totalCount'] = statDict['Total']['dCount'] +\
        statDict['Total']['ndCount']
    statDict['Total']['skipCount'] = statDict['Total']['dSkipCount'] +\
        statDict['Total']['ndSkipCount']
    statDict['Total']['Pass'] = statDict['Total']['dPass'] +\
        statDict['Total']['ndPass']
    statDict['Total']['runCount'] = statDict['Total']['totalCount'] -\
        statDict['Total']['skipCount']

    return statDict

def _transform_to_percent(statDict: dict) -> dict:
    """
    Function to convert the counts to percentage

    Args:
        statDict (dict): Dictionary containing the stats.

    Returns:
        dictionary now transformed to percentage.
    """
    # Go component-wise and transform the counts to percentage.
    tStatDict = copy.deepcopy(statDict)

    for component in statDict:
        if statDict[component]['ndPass'] -\
            statDict[component]['ndSkipCount'] != 0:
            tStatDict[component]['ndPass'] = ((statDict[component]['ndPass'])/\
                (statDict[component]['ndPass'] -\
                    statDict[component]['ndSkipCount']))*100
        if statDict[component]['dPass'] -\
            statDict[component]['dSkipCount'] != 0:
            tStatDict[component]['dPass'] = ((statDict[component]['dPass'])/\
                (statDict[component]['dPass'] -\
                    statDict[component]['dSkipCount']))*100
        if statDict[component]['runCount'] != 0:
            tStatDict[component]['Pass'] = ((statDict[component]['Pass'])/\
                statDict[component]['runCount'])*100
    return tStatDict

def _data_to_xls(statDict: dict, resultDict: dict, filePath: str,
                 totalRTime: str):
    """
    Function to prepare a spreadsheet using the data for
    results.

    Args:
        statDict (dict): The dict containing the test run numerical stats.
        resultDict (dict): The dict containing the test result metadata.
        filePath (str): File path of spreadsheet.
        totalRTime (str): Total runtime of the framework.
    """
    # Create mapping for the keys to description to be put in the sheet.
    rMap = [
        {'dCount': 'Disruptive Tests'},
        {'ndCount': 'Non Disruptive Tests'},
        {'dSkipCount': 'Disruptive Tests Skipped'},
        {'ndSkipCount': 'Non Disruptive Tests Skipped'},
        {'runCount': 'Tests Ran'},
        {'skipCount': 'Tests Skipped'},
        {'totalCount': 'Total Tests'},
        {'dPass': 'Disruptive Tests Pass Percentage'},
        {'ndPass': 'Non Disruptive Tests Pass Percentage'},
        {'Pass': 'Total Pass Percentage'}]
    topicList = ['S. No.', 'Test Name', 'Nature', 'Volume Type',
                 'Result', 'Time (hh:mm:ss)']
    # Create a workbook.
    wb = Workbook()

    # Populate the stats
    style = xlwt.easyxf('font: bold 1')
    for component in statDict:
        row = 0
        tR = wb.add_sheet(component)
        tDict = statDict[component]
        for subDict in rMap:
            for key, val in subDict.items():
                tR.write(row, 0, val, style)
                tR.write(row, 1, tDict[key])
            row += 1

    # Writing total runtime in the Total sheet.
    tR = wb.get_sheet('Total')
    timeVal = _time_rollover_conversion(totalRTime, True)
    tR.write(row, 0, "Total Time", style)
    tR.write(row, 1, timeVal)

    rowDiff = row+2
    # Populating the test data to the sheets.
    for component in resultDict:
        tR = wb.get_sheet(component)
        row = rowDiff
        # Add the topics.
        col = 0
        for topic in topicList:
            tR.write(row, col, topic, style)
            col += 1

        row += 1
        s_no = 1
        for nature in resultDict[component]:
            testsDict = resultDict[component][nature]
            for test in testsDict:
                for volType in testsDict[test]:
                    volData = testsDict[test][volType]
                    tR.write(row, 0, s_no)
                    tR.write(row, 1, test)
                    tR.write(row, 2, nature)
                    tR.write(row, 3, volType)
                    tR.write(row, 4, volData['testResult'])
                    timeVal = _time_rollover_conversion(volData['timeTaken'])
                    tR.write(row, 5, timeVal)
                    s_no += 1
                    row += 1

    # Push the changes to the file.
    wb.save(filePath)

def handle_results(resultQueue, totalTime: float, filePath: str=None):
    """
    Function to handle the results for redant.

    Args:
        resultQueue: It is a queue containing the test run results.

    Optional:
        filePath (str): The path wherein the result is to be stored
        if the output format is for xls.
    """
    # Transform queue data to dictionary.
    resultDict = _transform_queue_to_dict(resultQueue)

    # Obtain the statistics for further use.
    statDict = _obtain_stat(resultDict)

    # Convert the pass values to percentage.
    statDict = _transform_to_percent(statDict)

    # Output the result.
    if filePath is not None:
        _data_to_xls(statDict, resultDict, filePath, totalTime)
