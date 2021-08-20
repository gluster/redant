# Redant Logging.

Redant logging is achieved with the help of the `Logger` class which currently
consists of three methods,
1. set_logging_options
2. get_logger_handle

Following are certain design decisions taken,
1. The default logging level be it during the intitialization or logging is Info
as statistically speaking that is what would happen most of the time. Hence 
whoever calls the methods, `set_logging_options` can skip the final
parameter i.e. the log-level.
2. The log levels to be used by the user while invoking the methods are as follows,

	| Log level | Parameter |
	|:---------:|:---------:|
	|   Debug   |    'D'	|
	|   Info    |    'I'	|
	|   Error   |    'E'    |
	|   Warning |    'W'    |
	|  Critical |    'C'    |

## NOTE
Deprecated point - 3. One important design consideration is the usage of the logger APIs. 
Now the usual way is to invoke logger.debug or logger.info depending on the logging levels, but
this seems to be a little less generic, so `rlog` was created to handle this.
 A user using the logger function would just need to invoke `rlog(<log_message>, <log_level>)`
 The internal mapping to the logger's API calls will be done by rlog with the help of
a dictionary.

### Reasoning
The reason as to why the above decision was overturned is that the logging module
in python will dynamically take the file, linenumber and the API and that'd cause 
these values to default to relog component if we try to create a generic function
as the call to the logger's functions i.e. `logger.debug`, `logger/info`, etc. will
be done inside this module. Now once can pass on these values to the generic function
but that'd require us to invoke the inspect function will adds it's own overhead
as it has to find the elements present inside the given module at runtime after
parsing the file. ( As Tony would say..Not a great plan ). If we had dealt with 
a complied language then this would have been a good way of generic approach to
handling logging.

# Logging format:

All log messages MUST include:
* The cmd that is/was executed
* The machine(s) on which the command is/was executed

Ex: 

```python
self.logger.info(msg)

```
On starting the execution of cmd on a node:
```python
 self.logger.info( f"Running { cmd } on node { node }")
```
On completing the execution:
```python
 self.logger.info( f"Successfully ran { cmd } on { node } ")
```
## Log levels
=============
 Currently the best practice is to use info logs judiciously so that only required information is added to the logs most of the times. Repeated data and big data dumps need to be put under debug log
