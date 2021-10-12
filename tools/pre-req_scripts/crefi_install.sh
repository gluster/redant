#!/bin/sh
pip3 uninstall -y crefi
mkdir /tmp/crefi_repo
cd /tmp/crefi_repo
git clone https://github.com/vijaykumar-koppad/Crefi.git
cd Crefi
python3 setup.py install
cd /
rm -rf /tmp/crefi_repo