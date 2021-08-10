#!/bin/sh

# Flake runs
flake8 $(pwd) --ignore=C901,F811,F841,E722,E226,E402,W503,W605 --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 $(pwd) --ignore=C901,F811,F841,E722,E226,E402,W503,W605 --count --max-complexity=10 --max-line-length=79 --statistics

# Pylint runs
pylint --rcfile=$(pwd)/.pylintrc $(pwd)/core/
pylint --rcfile=$(pwd)/.pylintrc $(pwd)/common/
pylint --rcfile=$(pwd)/.pylintrc $(pwd)/tests/
