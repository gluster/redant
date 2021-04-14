#!/usr/bin/bash

# NARGS stores the number of arguments passed
# If the number of arguments passed is more than one
# Then it means the user has passed some operation specifically
NARGS=$#

# FILE(s) PATH stores the path of the file
FILEPATH=$1

# By default it will do both linting and flaking
# If passed flake, it will only flake
# If passed lint, it will only lint
OPERATION=$2

perform_linting () {
    if [ $FILEPATH == '.' ]
    then
        pylint -j 4 --rcfile=.pylintrc ./core
        pylint -j 4 --rcfile=.pylintrc ./core/parsing
        pylint -j 4 --rcfile=.pylintrc ./tests/example
        pylint -j 4 --rcfile=.pylintrc ./tests/example/sample_component
        pylint -j 4 --rcfile=.pylintrc ./tests/functional
        pylint -j 4 --rcfile=.pylintrc ./tests/functional/glusterd
        pylint -j 4 --rcfile=.pylintrc ./support
        pylint -j 4 --rcfile=.pylintrc ./support/ops/gluster_ops
        pylint -j 4 --rcfile=.pylintrc ./support/ops/support_ops
    else
        pylint -j 4 --rcfile=.pylintrc $FILEPATH
    fi
}

if [ $OPERATION == '' ]
then
    echo 'Nothing was passed in operation'
    echo 'Performing both flaking and linting'
    echo 'Flaking'
    flake8 $FILEPATH
    printf '\n==================================================\n'
    echo 'Linting'
    perform_linting
    printf "\n\n\nDone Flaking and Linting\n"
    echo '=============================================================='
    echo 'Run the following command to automatically remove most issues'
    echo '=============================================================='
    echo 'autopep8 -i PATH/TO/FILE.py'

elif [ $OPERATION == 'flake' ]
then
    echo "Performing " $OPERATION
    flake8 $FILEPATH
else
    echo "Performing " $OPERATION
    perform_linting

fi