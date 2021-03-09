"""
The thread runner is responsible for the execution of a given TC.
"""

from redant_libs.support_libs.relog import Logging


if __name__ == "__main__":
    # Create the logger object.
    logger = Logging.set_logging_options()

    # Create remote connection with the servers and clients.
    logger.info("Creating the remote connection")
