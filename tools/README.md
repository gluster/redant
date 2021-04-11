# Tools

Following tools files are present to make like easier for the user.

1. `clean_pycache` : A BASH script which clears out the cache files from the
project directories. This is helpful in getting an idea as to how much time
it'd take for the test suite to run in a CI environment wherein there won't
be any precompiles cache files.

2. `run_all_tests` : BASH script which runs the complete suite of tests. The 
path for the config file is taken as config/config.yml and the path as to
where the test cases will reside will be tests/ . Once can provide a flag
-nc if they want the TC suite to run faster as it won't clear the cache files.
This scenario might come handy wherein a user might want to test out some code
changes and see if it passes the sanity checks.
