# Result Handler

This component deals with the result formatting and presentation for the framework. 

## Output format
================

The output consists of three things(shown in the form of tables):

1. the volume type on which the test was run.
2. the test result - `PASS` or `FAIL`
3. the time taken by the test to run(in seconds).

```console
Table:
test_sample

+-------------+-------------+--------------------+
| Volume Type | Test Result |  Time taken (sec)  |
+-------------+-------------+--------------------+
```
---
There are two formats used by the framework to display the results:
1. Using the standard output (CLI-based)
2. Storing the output in a file 
---

### 1. Using the standard output (stdout)
This format is used when the `rf` flag is not set. 

Ex: 
```console
(venv) [root@server redant]# python3 -m core.redant_main -c ./core/parsing/config.yml -t tests/example/
```
In this format, the output is displayed on the <b>CLI</b>.

### 2. Storing the output in a file
This format is used when the `rf` flag is provided with the file path to store the result. Ex:
```console
(venv) [root@server redant]# python3 -m core.redant_main -c ./core/parsing/config.yml -t tests/example/  -rf "/PATH/TO/THE/RESULT/FILE"
```
In this format the output is stored in the file whose path is specified above.
