## How to decide the test nature

Redant test cases can be classified into two types,
1. Disruptive test cases (hereon referred to as Dtc)
2. Non-Disruptive test cases (hereon referred to as NDtc)

Based on the design of redant, NDtcs are run paralelly while Dtcs are run sequentially. So, how does one decide whether the test case they're writing is a NDtc or a Dtc ?

Following are some pointers which describe a Dtc. If a test case satisfies even one of the stated points, it is Dtc. For a test case to be NDtc, it shouldn't satisfy any of the stated points.

* The test case reboots a node ( server or client ).
* The test case reconfigures ports or changes firewalld rules.
* The test case is unmounting the client mountpoints and volume bricks itself.
* The test case changes cluster-level config parameters.
* The test case kills/stops/restarts glusterd in a node.
* The test case aims to create a huge amount of volumes, snapshots, geo-rep sessions or gfind sessions. [ The langauge here is a little vague and the reason behind that is we don't have a benchmarked value for what is huge amount of volumes or high IO.]