# redant

Design Doc Link : [Gluster-test Design-doc](https://docs.google.com/document/d/1D8zUSmg-00ey711gsqvS6G9i_fGN2cE0EbG4u1TOsaQ/edit?usp=sharing)

The architects of any project won't be there forever with it 
( not everyone has the luxury to be a BDFL ), hence it is important to have 
the thought process documented so that one doesn't need to go through the code. 
We for one believe in proper documentation. The very idea of developers and 
engineers being spartans who understand logic only from code is what we feel as 
. We need to be civilized humans and make it easy for the next person coming 
in to just glance at what it is, why it is and how it is.

# Readme Docs
For those who want to take the red pill, this is where you go, the Readme index
contains all the thought process, decision making and everything documented 
right from a variable, data structure to why some things are the way they are.
So if you are ready to take the leap to learn the ugly truth ( kidding! ),
this is where you go. But on the other hand, if you just want to learn about
how to get things running and that's it, take the blue pill.

* [Red Pill Index](./docs/RPIndex.md)
* [Blue Pill Index](./docs/BPIndex.md)

# Contents
* [Structure](#structure)
* [Set up](#set-up)
* [About](#flags)

## Structure:

core: contains the core redant framework which includes parsing,
test_list_builder, test_runner, runner_thread and redant_main.<br>
common: consists of the libs and ops that will help in running the
test cases and the mixin class.<br>
tests: holds the test cases as performace and functional tests and includes
abstract test. Add any new test cases here.<br>

## Set up

### To start Working:

1. Clone redant repo.

2. Populate the conf.yaml with relevant server and client details..


### STEP-BY-STEP procedure to run:
1. git clone `[your fork for this repo]`
2. Create a virtual environment : `virtualenv <virtual_env_name>`
3. Activate the virtual-env : `source <virtual_env_name>/bin/activate`
4. cd `[the-fork]`
5. Run `pip3 install -r requirements.txt`
6. To run the sample TC, just run the below cmd after populating the
config file with relevant values. The command has to be run from the main redant
reository. The tests path should be given with respect to the redant directory.
`python3 ./core/redant_main.py -c ./core/parsing/config.yml -t tests/example/`
7. Log files can be found at /tmp/redant.log [ default path ].
For more options, run `python3 ./core/redant_main.py --help`

The logging is specific to a TC run. So when a user gives a specific base dir
for logging when invoking `redant_main.py`, that directory will inturn
contain the following dirs,
 -> functional
 -> performance
 -> example

Now, based on the invocation, directory of a component will be created inside
the functional and performace dirs. And inside the component directory,
the Test case specific directory will be created which inturn will contain
volume specific log files.
So for example to see the log files of a test case which is,
`tests/functional/glusterd/test_sample_glusterd.py`
one would have to go to the directory,
`<base_log_dir>/functional/glusterd/test_sample_glusterd/`, which will inturn
contain the log files specific to volume type.

In addition to running TCs from within a suite, either performance or
functional or even under a more granular level of component, one can select to
run a specific TC also. To do this, one simply has to use the `-sp` flag while
invoking redant and instead of the directory path provide the path of the TC.
For example,
`python3 core/redant_main.py -c core/parsing/config.yml -t tests/example/sample_component/test_sample.py -sp`

One can also run the scripts given under the tools dir which will reduce the
lengthy commands to be typed out everytime. Check out the README.md at the link
[Tools-README](./tools/README.md)

## Those looking to get into the action of migratingtest cases.

Please refer the doc : [migratingTC.md](./docs/BP/migratingTC.md)

### Flags

* -c, --config : Stores the path of the config file(s) to read. You need to provide the path else by default it is `None`. Moreover, this is a required argument so you need to provide it for sure.
* -t, --test-dir : The path of the test directory where test cases exist. You can also provide the path to the specific test file. But in that case remember the `-sp` flag :upside_down_face:. This is also a required argument so don't forget it.
*   -l, --log-dir : It stores the path of the log directory where you want the log files to be kept. By default it stores `/tmp/redant` and it is not a required argument.
* -ll, --log-level : The log level you want for the execution.By default the log level is `I` (INFO). There are other log levels also like `D`(DEBUG), `W`(WARN) etc.
* -cc, --concurrency-count : It stores the number of concurrent tests run. By default it is 4.
* -rf, --result-file : It stores the path of the result file. By default it is `None`
* -xls, --excel-sheet : It stores the path of the excel sheet. By default it is `None`.
