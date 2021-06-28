"""
This component handles the
results in two ways:

1. display on the CLI
2. store in a file
"""
import xlwt
from xlwt import Workbook
from prettytable import PrettyTable
from colorama import Fore, Style


class ResultHandler:

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

        for item in test_results:
            if colorify:
                cls.result = (f"{cls.result} {Fore.BLUE}{item}\n")
                cls.result = (f"{cls.result} {Style.RESET_ALL}\n")
            else:
                cls.result = (f"{cls.result} {item}\n")

            table = PrettyTable(
                ['Volume Type', 'Test Result', 'Time taken (sec)',
                 'Skip Reason'])

            if test_results[item][0]['tcNature'] == 'disruptive' and\
                    test_results[item][0]['testResult'] is not None:
                dtest += 1
            elif test_results[item][0]['tcNature'] == 'nonDisruptive' and\
                    test_results[item][0]['testResult'] is not None:
                ndtest += 1
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
                else:
                    skip_reason = each_vol_test['skipReason']
                table.add_row(
                    [each_vol_test['volType'], each_vol_test['testResult'],
                     each_vol_test['timeTaken'], skip_reason])

            cls.result = (f"{cls.result}{str(table)}\n\n")

        table = PrettyTable(['Category',
                             'Cases',
                             'Pass Percent'])

        table.add_row(['nonDisruptive', ndtest,
                       0 if ndcount == 0 else (ndpass/ndcount)*100])
        table.add_row(['Disruptive', dtest,
                       0 if dcount == 0 else (dpass/dcount)*100])
        table.add_row(['Total', ndtest+dtest,
                       (0 if (ndcount + dcount == 0)
                        else ((ndpass + dpass)/(ndcount + dcount))*100)])

        cls.result = (f"Summary:\n{str(table)}\n{cls.result}\n")

        cls.result = (f"{cls.result}\nFramework runtime : {total_time}\n")

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

        for item in test_results:
            if test_results[item][0]['tcNature'] == 'disruptive' and\
                    test_results[item][0]['testResult'] is not None:
                dtest += 1
            elif test_results[item][0]['tcNature'] == 'nonDisruptive' and\
                    test_results[item][0]['testResult'] is not None:
                ndtest += 1

            for each_vol_test in test_results[item]:

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
        result_sheet.write(row, 0, 'Total')
        result_sheet.write(row, 1, ndtest + dtest)
        result_sheet.write(row, 2,
                           (0 if (ndcount + dcount == 0)
                            else
                            ((ndpass + dpass)/(ndcount + dcount))*100))

        row += 2

        result_sheet.write(row, 0, 'Total time taken (s)', style)
        result_sheet.write(row, 1, total_time)
        row += 2

        for item in test_results:
            result_sheet.write(row, 0, item, style)
            row += 1
            result_sheet.write(row, 0, 'Volume Type', style)
            result_sheet.write(row, 1, 'Test Result', style)
            result_sheet.write(row, 2, 'Time Taken (s)', style)
            result_sheet.write(row, 3, 'Skip Reason', style)
            row += 1

            for each_vol_test in test_results[item]:
                result_sheet.write(row, 0, each_vol_test['volType'])
                result_sheet.write(row, 1, each_vol_test['testResult'])
                result_sheet.write(row, 2, each_vol_test['timeTaken'])
                if each_vol_test['testResult'] is None:
                    result_sheet.write(row, 3, each_vol_test['skipReason'])
                else:
                    result_sheet.write(row, 3, "N/A")
                row += 1

            row += 2

        wb.save(excel_sheet)

    @classmethod
    def handle_results(cls, result_queue, result_path: str, total_time: float,
                       excel_sheet: str):
        """
        This function handles the results
        for the framework. It checks
        whether the results need to be
        shown in CLI or stored in a file
        specified by the user

        Args:
        result_queue: a queue of results
        result_path: path of the result file
        total_time: stores the total time taken by the framework
        excel_sheet: stores the path of the excel sheet
        """
        test_results = {}

        while not result_queue.empty():

            curr_item = result_queue.get()
            key = list(curr_item.keys())[0]
            value = curr_item[key]

            if key not in test_results.keys():
                test_results[key] = []

            test_results[key].append(value)

        if result_path is None:
            cls._display_test_results(test_results, total_time)
        else:
            cls._store_results(test_results, result_path, total_time)

        if excel_sheet is not None:
            cls.store_results_in_excelsheet(
                excel_sheet, test_results, total_time)
