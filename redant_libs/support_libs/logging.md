# Redant Logging.

Redant logging is achieved with the help of the `Logger` class which currently
consists of three methods,
1. set_logging_options
2. rlog
3. get_logger_handle

Wherein the set_logging_options and get_logger_handle are static methods while
rlog is a class method. The current design is a little convoluted as it exposes
the logger object to the outside world which has to be rectified. If one looks
into the class we have a `has a` relation between our logger object and the 
logger class. ( I admit this isn't the best way. So, when you are reading this
do see a big NEON light todo..)

Following are certain design decisions taken,
1. The default logging level be it during the intitialization or logging is Info
as statistically speaking that is what would happen most of the time. Hence 
whoever calls the methods, `set_logging_options` and `rlog` can skip the final
parameter i.e. the log-level.
2. The log levels to be used by the user while invoking the methods are as follows,

	| Log level | Parameter |
	|:---------:|:---------:|
	|   Debug   |    'D'	|
	|   Info    |    'I'	|
	|   Error   |    'E'    |
	|   Warning |    'W'    |
        |   Critical |   'C'    |

3. One important design consideration is the usage of the logger APIs. Now the usual 
way is to invoke logger.debug or logger.info depending on the logging levels, but
this seems to be a little less generic, so `rlog` was created to handle this.
 A user using the logger function would just need to invoke `rlog(<log_message>, <log_level>)`
 The internal mapping to the logger's API calls will be done by rlog with the help of
a dictionary.

# TODO:
1. Making the logger more object oriented. Re-think the current design of how
the class is.
        
