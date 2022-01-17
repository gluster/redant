# redant

[![Open in Visual Studio Code](https://open.vscode.dev/badges/open-in-vscode.svg)](https://open.vscode.dev/gluster/redant)

```console
    ____  __________  ___    _   ________
   / __ \/ ____/ __ \/   |  / | / /_  __/
  / /_/ / __/ / / / / /| | /  |/ / / /   
 / _, _/ /___/ /_/ / ___ |/ /|  / / /    
/_/ |_/_____/_____/_/  |_/_/ |_/ /_/     
                                         

usage: redant_main.py [-h] -c CONFIG_FILE -t TEST_DIR [-l LOG_DIR] [-ll LOG_LEVEL]
                      [-cc CONCUR_COUNT] [-xls EXCEL_SHEET][--show-backtrace] [-kold]

Redant test framework main script.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_FILE, --config CONFIG_FILE
                        Config file(s) to read.
  -t TEST_DIR, --test-dir TEST_DIR
                        The test directory where TC(s) exist
  -l LOG_DIR, --log-dir LOG_DIR
                        The directory wherein log will be stored.
  -ll LOG_LEVEL, --log-level LOG_LEVEL
                        The log level. Default log level is Info
  -cc CONCUR_COUNT, --concurrency-count CONCUR_COUNT
                        Number of concurrent test runs. Default is 2.
  -xls EXCEL_SHEET, --excel-sheet EXCEL_SHEET
                        Spreadsheet for result. Default value is NULL
  --show-backtrace      Show full backtrace on error
  -kold, --keep-old-logs
                        Don't clear the old glusterfs logs directory during environment setup.
                        Default behavior is to clear the logs directory on each run.
```

## Tested and Supported Distros

 | Distro | Redant | Gluster Server | Gluster Client |
 | :----: | :----: | :------------: | :-------------:|
 |Fedora 32| :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |
 |Fedora 34|:heavy_check_mark: | :heavy_multiplication_x: | ✖️ |
 |RHEL 7.9| :heavy_multiplication_x: | :heavy_check_mark: | :heavy_check_mark:|
 |RHEL 8.4| :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |

The architects of any project won't be there forever with it 
( not everyone has the luxury to be a BDFL ), hence it is important to have 
the thought process documented so that one doesn't need to go through the code. 
We for one believe in proper documentation. The very idea of developers and 
engineers being spartans who understand logic only from code is what we feel as 
. We need to be civilized humans and make it easy for the next person coming 
in to just glance at what it is, why it is and how it is.

Before trying out redant, do check the [known issues](./docs/known_issues.md) section

For those who want a pure markdown experience and a deeper dive...


# Readme Docs
The Documentation index can be found at [Docs](./docs/README.md)

# Contents
* [Set up](#set-up)
* [Those looking to get into the action of migrating test cases](#those-looking-to-get-into-the-action-of-migrating-test-cases)
* [Detailed Design](#design-document)

## Set up

### Pre requisites:
1. Passwordless ssh between all (to self as well) the nodes in the cluster.
2. Gluster installed on all the nodes and the bricks which would be used in the volumes,
are created on all the servers.
3. The following packages should be installed on all the nodes in the cluster, it includes
some packages which are required by external tools used in some test cases:
  1. git
  2. make
  3. gcc
  4. autoconf
  5. automake
  6. cronie
  7. rsync
  8. numpy
  9. sh

### To start Working:

1. Clone redant repo.
2. Populate the [config.yml](./config/config.yml) with relevant server and client details.


### STEP-BY-STEP procedure to run:
1. git clone `[your fork for this repo]`
2. Create a virtual environment using :
`virtualenv <virtual_env_name>` or
`python3 -m venv <virtual-env-name>`
3. Activate the virtual-env : `source <virtual_env_name>/bin/activate`
4. cd `[the-fork]`
5. Run `pip3 install -r requirements.txt`
6. Install the packages needed by some TCs by running the scripts under
[`tools/pre-req_scripts`](./tools/pre-req_scripts)
7. To run the sample TC, just run the below cmd after populating the
config file with relevant values. The command has to be run from the main redant
reository. The tests path should be given with respect to the redant directory.
`python3 ./core/redant_main.py -c ./config/config.yml -t tests/example/`
For more options, run `python3 ./core/redant_main.py --help`
8. Log files can be found at /var/log/redant/ [ default path ].

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
`functional/<gluster_component>/<test_name>/test_sample.py`
one would have to go to the directory,
`<base_log_dir>/<time_stamp>/functional/<gluster_component>/test_sample`, 
which will inturn contain the log files specific to volume type.

In addition to running TCs from within a suite, either performance or
functional or even under a more granular level of component, one can select to
run a specific TC also.
For example,
`python3 core/redant_main.py -c config/config.yml -t tests/example/sample_component`

One can also run the scripts given under the tools dir which will reduce the
lengthy commands to be typed out everytime. Check out the README.md at the link
[Tools-README](./tools/README.md)

## Those looking to get into the action of migrating test cases

Please refer the doc : [migratingTC.md](./docs/BP/Tools/migratingTC.md)

## Design Document

[Redant Design Doc](https://docs.google.com/document/d/1oJvUvvtfE5G8WlhFOg_gFbJwO2Ua7uCq12teqrjmwVU/edit?usp=sharing)
