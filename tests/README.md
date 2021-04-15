# Test Cases.

1. [About](#about)
2. [How to write a test case](#how-to-write-a-test-case)

## About
The TCs are divided into
1. Functional
2. Performance

Inside these categories we have sub-category depending on the gluster
component being tested in the given TC.

### Points of consideration while writing TC:
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

<a href="write"></a>

## How to write a test case

1. [Remember these points before writing a test case](#points-of-consideration-while-writing-tc)
2. Do add a docstring specifying what the test case does.
```js

This file contains a test-case which tests glusterd
starting and stopping of glusterd service.

```

3. Add the test type(disruptive or non-disruptive) and volume.
```js
Disruptive: disruptive
Non-disruptive: nonDisruptive
```

4. Import [ParentTest](https://github.com/srijan-sivakumar/redant/blob/main/tests/parent_test.py)

```js
from tests.parent_test import ParentTest
```

5. Create a class that extends the `ParentTest`.
```js
class TestCase(ParentTest):
```

6. Make a function `run_test`. This function basically overrides the run test function from the [Parent Test](https://github.com/srijan-sivakumar/redant/blob/main/tests/parent_test.py)

```js
def run_test(self, redant):
```

7. Add the step by step operation in docstrings so that it would be easier for you to cross-check as well as in understanding for any other person looking at the test case.

8. Now add the code to test the functionalities.