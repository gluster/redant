# Test Cases.

The TCs are divided into
1. Functional
2. Performance

Inside these categories we have sub-category depending on the gluster
component being tested in the given TC.

Points of consideration while writing TC:
1. The naming of the TCs should be prefixed with test_
2. The type of the TC ( disruptive or non-disruptive ) and the
types of volumes for which it'll be run has to be part of a TC. On referring
the test_sample.py one can see that right after the module comment, a single
line comment has been added which is of the form

`#tc_type;volType1,volType2`

herein the tc_type can be `disruptive` or `nonDisruptive` and the volTypes are
as follows

| volType | Actual Volume type |
| :-----: | :----------------: |
|  dist   |  Distributed       |
|  rep    |  Replicated        |
|  arb    |  Arbiter           |
|  disp   |  Dispersed         |
|  dist-rep | Distributed-Replicated |
|  dist-arb | Distributed-Arbiter |
|  dist-disp | Distributed-disp |

If the TC doesn't deal with any volume creation or if the user wants the TC
to deal with multiple TCs in a single run itself then the following is the
format
`#tc_type'`

This data will be parsed by the test list builder so as to determine how many
threads for this TC has to be created and if it can be run parallely with other
TCs.
