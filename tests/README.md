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
the sample_tc.py one can see that right after the module comment, a single
line comment has been added which is of the form

`#tc_type;volType1,volType2`

This data will be parsed by the test list builder so as to determine how many
threads for this TC has to be created and if it can be run parallely with other
TCs.
