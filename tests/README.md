# Test Case

1. [About](#about)
2. [How to write a test case](#how-to-write-a-test-case)

## About
The TCs are divided into
1. Functional : These tests are basically to test the working of the functionalities.
2. Performance : Performance tests deals with the performance i.e. *how fast is this working* :zap:

Inside these categories we have sub-category depending on the gluster
component being tested in the given TC.

### Points of consideration while writing TC:
1. The naming of the TCs should be prefixed with **test_**
2. The type of the TC ( disruptive or non-disruptive ) and the
types of volumes for which it'll be run has to be part of a TC. On referring
the test_sample.py one can see that right after the module comment, a single
line comment has been added which is of the form

`#tc_type;volType1,volType2`

herein the tc_type can be :
1. `disruptive` : The test that affect the cluster.
2. `nonDisruptive` : The test that does not affect the cluster.

and the volTypes are as follows:

| volType | Actual Volume type |
| :-----: | :----------------: |
|  dist   |  Distributed       |
|  rep    |  Replicated        |
|  arb    |  Arbiter           |
|  disp   |  Dispersed         |
|  dist-rep | Distributed-Replicated |
|  dist-arb | Distributed-Arbiter |
|  dist-disp | Distributed-disp |

---
A brief about these volumes:
* Distributed : Distributed volumes distribute files across the bricks in the volume. 
* Replicated :  Replicated volumes replicate files across bricks in the volume.
* Arbiter : In this type of volume, quorum is taken into account at a brick level rather than per file basis. 
* Dispersed : Dispersed volumes are based on erasure codes, providing space-efficient protection against disk or server failures. 
* Distributed-Replicated : Distributed replicated volumes distribute files across replicated bricks in the volume.
* Distributed Dispersed : Distributed dispersed volumes distribute files across dispersed subvolumes.

You can learn more about these volumes [here](https://docs.gluster.org/en/latest/Administrator-Guide/Setting-Up-Volumes/) and [here](https://docs.gluster.org/en/latest/Administrator-Guide/Thin-Arbiter-Volumes/)

---

If the TC doesn't deal with any volume creation or if the user wants the TC
to deal with multiple TCs in a single run itself then the following is the
format
`#tc_type'`

This data will be parsed by the test list builder so as to determine how many
threads for this TC has to be created and if it can be run parallely with other
TCs.


## How to write a test case

1. [Remember these points before writing a test case](#points-of-consideration-while-writing-tc)
2. Do add a docstring specifying what the test case does. This will not only 
help anyone else to understand what the test is meant for but will also help 
you in case you visit this test case later. Also, it saves time :watch: to understand the operation. 
```js
test_start_stop_glusterd.py
============================
"""
This file contains a test-case which tests glusterd
starting and stopping of glusterd service.
"""

```
So as you can see from the first few lines itself we understand what the test is meant for. :grin:

3. Add the test type(disruptive or non-disruptive) and volume type as well. This helps the framework to understand what kind of test is this and on which volumes this has to be tested on. This is done with the help of [Comment Parser](https://pypi.org/project/comment-parser/#:~:text=Python%20module%20used%20to%20extract,code%20files%20of%20various%20types.)

In the [Test List Builder](https://github.com/srijan-sivakumar/redant/blob/main/core/test_list_builder.py), these comments are extracted and then passed on to the next component of the framework in the form of a dictionary.
```js
    flags = str(extract_comments(tc_path, mime="text/x-python")[0])
    tc_flags = {}
    tc_flags["tcNature"] = flags.split(';')[0]
    tc_flags["volType"] = flags.split(';')[1].split(',')
```

For reference:

**Test type**

```js
Disruptive: `#disruptive`
Non-disruptive: `#nonDisruptive`
```

**Volume type:**

| volType | Actual Volume type |
| :-----: | :----------------: |
|  dist   |  Distributed       |
|  rep    |  Replicated        |
|  arb    |  Arbiter           |
|  disp   |  Dispersed         |
|  dist-rep | Distributed-Replicated |
|  dist-arb | Distributed-Arbiter |
|  dist-disp | Distributed-disp |


4. Now, import [AbstractTest](https://github.com/srijan-sivakumar/redant/blob/main/tests/abstract_test.py). Two questions that must come to your mind:
- What is this Abstract Test?
- Why to import it in every test? :space_invader:

[AbstractTest](https://github.com/srijan-sivakumar/redant/blob/main/tests/abstract_test.py), from the name itself it's almost clear that this test is abstract to all the tests or is the superclass for all other tests. It has the standard functions that the tests inherit and might even override.

The functions that it has:
* \_\_init\_\_() : This function not just acts as a constructor but also an initiator for each test case.
* run_test() : This will be overriden by the tests to perform the operation each test needs to perform.
* parent_run_test() : This function takes care of the exception handling for each and every test case and also calls the run_test function.
* terminate() : This function takes care of the tasks that need to be done in the end of each test case like closing the connections etc.

```js
from tests.abstract_test import AbstractTest
```

5. Create a class that extends the `AbstractTest`. This is important as we already know that all the tests need to follow a certain set of functionalities to be performed and rules to be followed to run them and these are all in the AbstractTest. Without this statement, you cannot override the run_test() function in your test.
```js
class TestCase(AbstractTest):
```

6. Make a function `run_test`. This function basically overrides the run_test() function(as mentioned earlier) from the [AbstractTest](https://github.com/srijan-sivakumar/redant/blob/main/tests/abstract_test.py). Whatever, operation you want to perform needs to be a part of this function. You don't need to take care of the exception handling part as this is already taken care of by the AbstractTest -> parent_run_test() function and hence all you need is call the ops and execute the functionalities. Moreover, remember to add `redant` as one of the arguments as it won't be able to override the run_test() function and you won't be able to call the ops without the redant object.

```js
def run_test(self, redant):
```
7. To test the operation you need to call the ops. For example, you need to test the start and stop glusterd operations.
```js
    redant.start_glusterd(self.server_list)
    redant.stop_glusterd(self.server_list)
```
Here, we are calling the `start_glusterd()` and `stop_glusterd()` ops using the `redant` object.
In the same way you can call the other ops and use them to write your own test.

### To know more about the Ops you can go [here](https://github.com/srijan-sivakumar/redant/blob/main/common/ops/OPS_README.md)

---

At last, don't forget to add the step by step operation in docstrings so that it would be easier for you to cross-check as well as in understanding for any other person looking at the test case. :smiley:

---
