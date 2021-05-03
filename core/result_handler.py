"""
This component handles the
results in two ways:

1. display on the CLI
2. store in a file
"""
from prettytable import PrettyTable
from colorama import Fore, Style


class ResultHandler:

    @classmethod
    def _get_output(cls, test_results: dict, colorify: bool, total_time: float):
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

        cls.result += (f"\nTotal time taken by the framework is {total_time}\n")        

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
    def _store_results(cls, test_results: dict, result_path: str, total_time: float):
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
    def handle_results(cls, result_queue, result_path: str, total_time: float):
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
