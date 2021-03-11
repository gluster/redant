# Redant

### Structure:

redant_libs: consists of the libs and ops that will help in running the test cases.<br>
tests: holds the test cases. Add any new test cases here.<br>

### To start Working:

1. Clone Redant repo.

2. Create a **Utilities** folder and add **conf.yaml** file.


### STEP-BY_STEP procedure to run:
1. git clone `[your fork for this repo]`
2. Create a virtual environment : `virtualenv <virtual_env_name>`
3. Activate the virtual-env : `source <virtual_env_name>/bin/activate`
4. cd `[the-fork]`
5. Run `pip3 install -r requirements.txt`
7. mkdir `Utilities` && touch `Utilities/conf.yaml`
8. Add the following in `conf.yaml`:

```javascript
host_list: [server IPs]
user: "user"
passwd: "pass"
```

9. Use the thread_runner.py to run the sample test case.
`python3 thread_runner.py -t tests/test_sample_tc.py -tf test_fn -c <path_to_conf_file>`.
10. Log files can be found at /tmp/redant.log [ default path ]. For more options, run `python3 thread_runner.py --help`
