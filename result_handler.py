from prettytable import PrettyTable

class ResultHandler:

    @classmethod
    def display_test_results(cls, test_results):
        
        print("Table:")

        for item in test_results:
            print(item)
            table = PrettyTable(['Volume Type','Test Result','Time taken'])
            for each_vol_test in test_results[item]:
                
                table.add_row([each_vol_test['volType'],each_vol_test['testResult'],each_vol_test['timeTaken']])
            
            print(table)