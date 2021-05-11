"""
This file consists of functions for handling 
signals. Signal handling is required for the
graceful exit of the test framework
"""

def signal_handler(signalNumber, frame):
    """
    Function for handling signal and raising the
    SystemExit call for graceful exit of the test 
    framework
    Args:
        signalNumber (int): The signal number of the signal caught
        frame: current stack frame, None or stack frame object.  
    """
    print("Signal Received",signalNumber)
    raise SystemExit('Exiting...')
    return
