import sys
# print(sys.path)
# sys.path.append("./redant_libs")
print(sys.path)
from redant_libs.peer_ops import (
    peer_probe
)

from odinControl.rexe.rexe import Rexe

from redant_libs.redant_resources import Redant_Resources as RR
from unittest import TestCase
import unittest

R = Rexe(conf_path="./Utilities/conf.yaml")

class TestPeerProbe(TestCase):

    def test_peer_probe(self):

        R.establish_connection()
        RR.rlogger.info("Started peer probe testing")
        ret = peer_probe('10.70.43.101','10.70.43.228')

        self.assertEqual(ret, 0, "Peer probe failed")
        RR.rlogger.info("Ended peer probe testing")


if __name__ == '__main__':
    unittest.main()
    