import sys

sys.path.append("./odinControl")

from redant_libs.support_libs.relog import Logging
    
class Redant_Resources(Logging):
   
    rlogger = Logging.set_logging_options(log_file_path='./redant.log',log_file_level='D')