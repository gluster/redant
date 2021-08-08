## How to decide the test nature

Redant test cases can be classified into two types,
1. Disruptive test cases (hereon referred to as Dtc)
2. Non-Disruptive test cases (hereon referred to as NDtc)

Based on the design of redant, NDtcs can be run paralelly while Dtcs have to be run sequentially. So, how does one decide whether the test case they're writing is a NDtc or a Dtc ?

Following are some pointers which describe a Dtc. If a test case satisfies even one of the stated points, it is Dtc. For a test case to be NDtc, it shouldn't satisfy any of the stated points.

* The test case reboots a node ( server or client ).
* The test case reconfigures ports or changes firewalld rules.
* The test case is unmounting the mountpoint which acts as glusterfs brick roots.
* The test case aims to create a huge amount of volumes, snapshots, geo-rep sessions or gfind sessions.