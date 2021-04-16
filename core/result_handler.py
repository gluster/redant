"""
This component is dedicated to
displaying the result of the tests
in the form of tables for better
understanding of the performance of
framework
"""
from prettytable import PrettyTable
from colorama import Fore, Style


class ResultHandler:

    @classmethod
    def _get_output(cls, test_results: dict, colorify: bool):
        """
        It generates the output in the
        form of tables with columns
        containing volume type, test result
        and the time taken to execute the test

        Args:
        test_results: All the tests result.
        colorify: Stores whether to show colored
                output or not
        """
        cls.result = "Table:\n"

        for item in test_results:
            if colorify:
                cls.result += (Fore.BLUE + item+"\n")
                cls.result += (Style.RESET_ALL+"\n")
            else:
                cls.result += (item+'\n')

            table = PrettyTable(
                ['Volume Type', 'Test Result', 'Time taken (sec)'])
            for each_vol_test in test_results[item]:

                table.add_row(
                    [each_vol_test['volType'], each_vol_test['testResult'],
                     each_vol_test['timeTaken']])

            cls.result += (str(table)+"\n")

    @classmethod
    def _display_test_results(cls, test_results: dict):
        """
        This function displays the test results
        in the form of tables.

        Args:
        test_results: All the tests results.

        """
        cls._get_output(test_results, True)
        print(cls.result)

    @classmethod
    def _store_results(cls, test_results: dict, result_path: str):
        """
        This function stores the test results
        in the form of tables in a file.

        Args:
        test_results: All the tests results.
        result_path: Path of the result file
        """
        cls._get_output(test_results, False)
        file = open(result_path, 'w')
        file.write(cls.result)
        file.close()

    @classmethod
    def handle_results(cls, test_results: dict, result_path: str):
        """
        This function handles the results
        for the framework. It checks
        whether the results need to be
        shown in CLI or stored in a file
        specified by the user

        Args:
        test_results: all the tests results
        result_path: path of the result file
        """
        if result_path is None:
            cls._display_test_results(test_results)
        else:
            cls._store_results(test_results, result_path)
