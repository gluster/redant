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
    def display_test_results(cls, test_results: dict):
        """
        This function displays the test results
        in the form of tables.

        Args:
        test_results: All the tests results.

        """
        print("Table:")

        for item in test_results:
            print(Fore.BLUE + item)
            print(Style.RESET_ALL)
            
            table = PrettyTable(['Volume Type','Test Result','Time taken'])
            for each_vol_test in test_results[item]:
                
                table.add_row([each_vol_test['volType'], each_vol_test['testResult'],each_vol_test['timeTaken']])
            
            print(table)