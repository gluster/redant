mkdir /tmp/arequal_repo
cd /tmp/arequal_repo
git clone https://github.com/nigelbabu/arequal.git
cd arequal
./autogen.sh
./configure
make
make install
rm -rf /tmp/arequal_repo