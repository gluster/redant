# High Level Design

Before diving into the analysis of how Redant is divided into smaller chunks of functions, we need to jot the points as to why such a framework was even required.
1. Testing a filesystem is not a cakewalk. If one were to look at the functionalities of a fs, there are the core functions which are to be provided 
( because these functionalities are what makes a fs, fs) and along with that data services such as data backup, snapshots, other metadata related operations. 
Add on to this the clustered nature of the offering, hence increased set of moving components impyling a greater permmutation and combination of testing 
of different features and situations. This implies a framework which takes up the testing should provide a rich set of libraries to cover these options.
2. Testing all these features will consume time. We cannot compromise on the number of tests run but it'll be also frustrating for an engineer to wait 
eons for the result to arrive even for a small change to the code base. This calls for parallelization of the test runs.
3. The file system being a clustered network fs demands that we work with a cluster of nodes for the testing. Hence commands have to be executed in the 
said nodes and not just synchronously, as there might be scenarios wherein we need to address asynchronous operations. Hence a robust remote command 
executioner segment but at the same time, not bloated.
4. The person who sits down with penning down a test case or even looking to improve the framework should be able to figure out the operations to be 
performed as well as the libraries and functions to be used with ease. Also, the project level dependencies should be easily resolved. Add to this the 
basic set of infrastructure required to run a single test case so that the engineer or developer can verify the test case or improvements before pushing 
to CI and reviews.
5.  The results provided should be easy to understand and maybe even exportable if in standard format. This also extends to the logging wherein we 
should be logging what is required and also in such a manner that it is easy to debug the failures.
6. To not to re-invent the wheel but at the same time not to paint the existing wheel. We needed to take feature sets and functionalities which 
were good candidates and also incorporate the ideas which help in improving the way test automation scripts are written, run and results analyzed.

With these right set of feature requirements in mind, following decisions were taken to be the core feature sets of Redant
1. Operational libraries with clear demarcation, reduced code duplicity and good set of functions to cover even the strangest of test scenarios.
2. Running test cases concurrently. But all tests cannot be run concurrently as certain test cases would perform operations which would lead 
to changes in the cluster which can cause other test cases to fail. This needs to be understood properly as certain operations when done concurrently 
in case of glusterfs shouldn't fail but some operations would certainly lead to failure in the allied scenarios. So test cases have to be marked as 
disruptive or non-disruptive wherein 
disruptiveness implies that the Test Case cannot be run concurrenctly with any other test case. Nonetheless, 
non-disruptive test cases running concurrently will slash down the time by a good factor.
3. The remote executioner mature enough to handle asynchronous as well as synchronous operations, wherein asynchronous results can be obtained 
whenever required by the test flow. Also reconnect mechanism to connect back to the said servers after reboots or conncetion failures.
4. The test list is created at runtime and it is at that moment the order of execution is to be decided based on the nature of the test cases.
5. Log file creations to be hierarchial. And every test case run will have its own log file. This will help in tracking the failures quickly 
rather than parsing over a big log file containing all failures. Also logging for success scenarios is frowned upon. The idea is to just state 
a certain operation is going to be performed and then if at all there is any exception, to log it but if it is a success scenario, we 
just continue on with the next set of execution.
6. Result handler to be able to give out the result in an orderly manner as stdout tables or even better, inside xls sheets which are easy to 
share the results. Also the time taken for each test run down to the level of volume type for which the test was run till the total time taken for the 
whole framework will be part of the analysis.


## Architectural components

Now that we have the important points hashed our, let us see how Redant looks architecturally. Redant's working can be easily 
understood if one were to divide it into three components,

1. Core
2. Commom
3. Tests


```
     Common                                 Tests
     +----------------------+               +------------------------------+
     | Operational libraries|               |             | Component1 TCs |
     | for IO and gluster   |               | Functional  | Component2 TCs |
     | related ops.         |               |             | Component3 TCs |
     +----------------------+               +-------------+----------------+
     | REXE | RELOG | VOLDS |               |             | Component1 TCs |
     +----------------------+               | Performance | Component2 TCs |
     |       MIXIN          |               |             | Component3 TCs |
     +----------------------+               +------------------------------+
                                            |       Abstract Test            |
                                            +------------------------------+
   
   
                     Core
                     +--------------------------------------------------+
                     | Result Handler | Test Runner | Test List Builder |   
                     +--------------------------------------------------+
                     | Config Handler | Environ |       Redant Main     |
                     +--------------------------------------------------+

```

## Core
As the name suggests, this is the core part of the test framework. The functionalities provided in core should not be performing any operation other than 
enabling an environment for the execution of test cases and handling their execution as well collecting the results and formatting and providing it in a proper
format. The core component is what a user would be interacting with whenever running the test suite, especially with `redant_main.py`.

## Common
The common consists of the features and the libraries required to write a test case, running it in the environment and handling the success and failure scenarios
of a test case execution. We are using mixin pattern here to expose the features of the common to be used by the core as well as the Tests. This is done not only
to simplify how the gluster specific operations are accessed but also saves us from the frustrating multiple import and muti object scenario. Also, these ops have
a horizontal dependency with each other which is easily solved by using Mixin. If at all any new operational support is to be added, this is where one has to come
and knock the doors.

## Tests
The actual entity which would run in the clusters. The instructions for these runs are added in the tests component. After the framework reaches a mature stage, 
most interactions a user might have is with the tests component ( and ops if new features are to be added. ). The tests are further divided into functional
and performance tests ( I guess the names are self explanatory ). And within these are sub-components which are usually the gluster specific classifications
such as 'Glusterd', 'Geo-replication', 'Snapshot', etc. Each sub-component will contain the test cases catering to different scenarios wherein the said
component figures in. All these test components are dependent upon the Common. Also, every test case derives some basic operational capability from a common
abstract test which lifts much of the repeated tasks usually done when a test case run begins and ends.

