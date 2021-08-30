## Catch All Exception

Projects grow over time and sometimes in ways in which it wasn't even planned for due to some change in initial assumption or new requirements. This means we might have not thought of an exception to be thrown in a scenario but with time code change now is liable to throw an exception, we might be in red as the code run will be spewing out a big traceback and dump when we are expecting it to gracefully handle the exceptions.

One of the ways this is being handled in redant is with the help of a catch all exception handler in redant_main over the main() call. This handler will catch any exception which has not been thought of. Now comes the question as to where this exception will be stored ? We don't know where redant will be failing, what if it fails even before the log initialization ? This would mean a rudimentary way of logging the exception and the traceback.

The location for this error and traceback is `/var/log/redant/redant-<timestamp>`. Along with putting this exception in file, there's also an indication which is put into stdout for where to find the traceback if there is any.
