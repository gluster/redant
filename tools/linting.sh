#!/bin/sh

FILEPATH='.'
perform_linting () {
    if [[ $FILEPATH == '.' ]]
    then
        pylint -j 4 --rcfile=.pylintrc ./core
        pylint -j 4 --rcfile=.pylintrc ./core/parsing
        pylint -j 4 --rcfile=.pylintrc ./tests/
        pylint -j 4 --rcfile=.pylintrc ./tests/example
        pylint -j 4 --rcfile=.pylintrc ./tests/example/sample_component
        pylint -j 4 --rcfile=.pylintrc ./tests/functional
        pylint -j 4 --rcfile=.pylintrc ./tests/functional/glusterd
        pylint -j 4 --rcfile=.pylintrc ./common
        pylint -j 4 --rcfile=.pylintrc ./common/ops/gluster_ops
        pylint -j 4 --rcfile=.pylintrc ./common/ops/support_ops
    else
        pylint -j 4 --rcfile=.pylintrc $FILEPATH
    fi
}

help_info () {
# Provides the help information
# Describes the flags and their usage
    echo
    echo "Linting help"
            echo "============="
            echo "Flags:"
            echo "-p : Specifies the path of the file"
            echo "    Ex: tools/linting.sh -p /home/redant/core"
            echo
            echo "-f : Specifies flake operation to be performed only"
            echo "    Ex: If you want to test flake for core"
            echo "        tools/linting.sh -p /home/redant/core -f"
            echo
            echo "-l : Specifies lint operation to be performed only"
            echo "    Ex: If you want to test lint for core"
            echo "        tools/linting.sh -p /home/redant/core -l"
            echo
            echo "-h : Provides the information about the flags"
            echo
            echo "Note:"
            echo "====="
            echo "If you don't specify the path, the operation will occur on the whole repo"
            echo
            echo "Ex: tools/linting.sh -f -l"
            echo "This will perform the linting on the whole repo"
            echo
            echo "Examples:"
            echo "========="
            echo "tools/linting.sh -f"
            echo "This will perform only flake on the folder"
            echo
            echo "tools/linting.sh -l"
            echo "This will perform only lint on the folder"
            echo
            echo "tools/linting.sh -p /home/redant/core -f -l"
            echo "This will perform linting on the folder"
            echo
            echo "tools/linting.sh -p /home/redant/core -f"
            echo "This will perform only flake operation on the folder"
            echo
            echo "tools/linting.sh -p /home/redant/core -l"
            echo "This will perform only lint operation on the folder"
            echo
            echo "tools/linting.sh -[wrong flag]"
            echo "This will show illegal action"
}

while getopts "p:flh" opt; do
    case $opt in
        p)
            if [[ $OPTARG == '' ]]
            then
                echo "No path specified."
                echo "Linting the whole repo"
            else    
                echo "Path File:"$OPTARG
                FILEPATH=$OPTARG
            fi
        ;;
        f)
            echo "Flake operation starts"
            flake8 $FILEPATH --ignore=C901,F811,F841,E722,E226,E402,W503,W605 --count --select=E9,F63,F7,F82 --show-source --statistics
            flake8 $FILEPATH --ignore=C901,F811,F841,E722,E226,E402,W503,W605 --count --max-complexity=10 --max-line-length=79 --statistics
        ;;
        l)
            echo "Lint operation starts"
            perform_linting
        ;;
        h)
            help_info

        ;;
        \?)
            help_info

        ;;
    esac
done
