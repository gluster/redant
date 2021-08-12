#!/bin/sh

# Flake runs
printf "Flake runs\n"
flake8 $(pwd) --ignore=C901,F811,F841,E722,E226,E402,W503,W605 --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 $(pwd) --ignore=C901,F811,F841,E722,E226,E402,W503,W605 --count --max-complexity=10 --max-line-length=79 --statistics

# Pylint runs
printf "Pylint result for core dir"
pylint --rcfile=$(pwd)/.pylintrc $(pwd)/core/

printf "Pylint result for common dir"
pylint --rcfile=$(pwd)/.pylintrc $(pwd)/common/

printf "Pylint result for tests dir"
pylint --rcfile=$(pwd)/.pylintrc $(pwd)/tests/
