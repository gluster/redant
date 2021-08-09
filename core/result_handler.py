"""
This component handles the
results in two ways:

1. display on the CLI
2. store in a spreadsheet
"""
import copy
import traceback
import xlwt
from xlwt import Workbook
from prettytable import PrettyTable


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
        tempDict['skipReason'] = testDict[tName]['skipReason']
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
        ndRuns = 0
        dRuns = 0

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
                    if disCrDict[test][volT]['testResult'] != "SKIP":
                        dRuns += 1
                    if disCrDict[test][volT]['testResult'] == "PASS":
                        dPass += 1
                    elif disCrDict[test][volT]['testResult'] == "SKIP":
                        dSkipCount += 1
        if "nonDisruptive" in crDict.keys():
            ndisCrDict = crDict['nonDisruptive']
            ndCount += len(list(ndisCrDict.keys()))
            for test in ndisCrDict:
                for volT in ndisCrDict[test]:
                    if ndisCrDict[test][volT]['testResult'] != "SKIP":
                        ndRuns += 1
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
        tempDict['dRuns'] = dRuns
        tempDict['ndRuns'] = ndRuns
        tempDict['totalRuns'] = dRuns + ndRuns
        tempDict['skipCount'] = dSkipCount + ndSkipCount
        if tempDict['totalRuns'] == 0:
            tempDict['runCount'] = 0
        else:
            tempDict['runCount'] = tempDict['totalRuns'] -\
                tempDict['skipCount']
        tempDict['dPass'] = dPass
        tempDict['ndPass'] = ndPass
        tempDict['Pass'] = dPass + ndPass
        statDict[component] = copy.deepcopy(tempDict)

    # Aggregating the component results in Total component.
    tempDict = {}
    for component in statDict:
        for key, val in statDict[component].items():
            if key not in tempDict.keys():
                tempDict[key] = 0
            tempDict[key] += val
    statDict['Total'] = copy.deepcopy(tempDict)
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
        if statDict[component]['ndRuns'] != 0:
            tStatDict[component]['ndPass'] =\
                (statDict[component]['ndPass']*100) /\
                (statDict[component]['ndRuns'])
        if statDict[component]['dRuns'] != 0:
            tStatDict[component]['dPass'] =\
                (statDict[component]['dPass']*100) /\
                (statDict[component]['dRuns'])
        if statDict[component]['totalRuns'] != 0:
            tStatDict[component]['Pass'] =\
                (statDict[component]['Pass']*100) /\
                (statDict[component]['totalRuns'])
    return tStatDict


def _data_to_xls(statDict: dict, resultDict: dict, filePath: str,
                 totalRTime: str, logger):
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
    topicList = ['Test Name', 'Nature', 'Volume Type',
                 'Result', 'Time (hh:mm:ss)', 'Skip Reason']
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
        for nature in resultDict[component]:
            testsDict = resultDict[component][nature]
            for test in testsDict:
                for volType in testsDict[test]:
                    volData = testsDict[test][volType]
                    tR.write(row, 0, test)
                    tR.write(row, 1, nature)
                    tR.write(row, 2, volType)
                    tR.write(row, 3, volData['testResult'])
                    timeVal = _time_rollover_conversion(volData['timeTaken'])
                    tR.write(row, 4, timeVal)
                    tR.write(row, 5, volData['skipReason'])
                    row += 1

    # Push the changes to the file.
    try:
        wb.save(filePath)
    except Exception as error:
        tb = traceback.format_exc()
        logger.error(f"XLS Save error : {error}")
        logger.error(f"XLS Save traceback : {tb}")

def _data_to_pretty_tables(statDict: dict, resultDict: dict,
                           totalRTime: str):
    """
    Function to provide the output in stdout pretty tables.

    Args:
        statDict (dict): The dict containing the test run numerical stats.
        resultDict (dict): The dict containing the test result metadata.
        totalRTime (str): Total runtime of the framework.
    """
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
    # Test case wise data display for
    # other components.
    for component in resultDict:
        if component == 'Total':
            continue
        print(f"Results for {component}")
        for nature in resultDict[component]:
            print(f"Test nature : {nature}")
            testDict = resultDict[component][nature]
            for test in testDict:
                print(f"TestName : {test}")
                tTable = PrettyTable(['Volume Type', 'Test Result',
                                      'Time Taken (hh:mm:ss)', 'Skip Reason'])
                for volType in testDict[test]:
                    volData = testDict[test][volType]
                    time_val = _time_rollover_conversion(volData['timeTaken'])
                    tTable.add_row([volType, volData['testResult'], time_val,
                                    volData['skipReason']])
                print(tTable)

    # Print the summary.
    totalTable = PrettyTable(['Category', 'Count'])
    totalVals = statDict['Total']
    for subDict in rMap:
        for key, value in subDict.items():
            totalTable.add_row([value, totalVals[key]])
    print(totalTable)
    totalTime = _time_rollover_conversion(totalRTime, True)
    print(f"Total Time Taken : {totalTime}")


def handle_results(resultQueue, totalTime: float, logger,
                   filePath: str = None):
    """
    Function to handle the results for redant.

    Args:
        resultQueue: It is a queue containing the test run results.
        totalTime: The total time taken for test case execution.
        logger: The logger object used for logging.

    Optional:
        filePath (str): The path wherein the result is to be stored
        if the output format is for xls.
    """
    logger.debug("Initializing result handling.")
    # Transform queue data to dictionary.
    resultDict = _transform_queue_to_dict(resultQueue)

    # Obtain the statistics for further use.
    statDict = _obtain_stat(resultDict)

    # Check for exclude test run.
    if statDict == {'Total': {}}:
        print("Requested test is in exclude list.")
        return

    # Convert the pass values to percentage.
    statDict = _transform_to_percent(statDict)

    # Output the result.
    if filePath is not None:
        logger.info(f"Results to be put inside : {filePath}")
        _data_to_xls(statDict, resultDict, filePath, totalTime, logger)
    else:
        logger.info("Results to be put to stdout")
        _data_to_pretty_tables(statDict, resultDict, totalTime)
