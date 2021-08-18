# Volume data structure (volds)

What prompted the creation of a data structure to store volume related
data in a test case run ?
To answer this in simpler terms, we needed a way to handle cleanups, addition,
removal, replacement of bricks, accessing mountpoints, volume options, etc.
Now, we can either query glusterfs everytime we require such operation but
wait...a test case should have a clearly defined operations which it is
supposed to perform and if we were to bring the collection of these data
whenever we need to perform any of the aforementioned actions, that'd mean
we are performing more gluster related operations.
Even if we were to ignore this, we still have to address the part wherein the
gluster related operations are performed remotely. This implies a some delay,
infinitesimal ( Not really..certain operations take time to be performed by 
gluster and then the result to be handed back to the shell env created by Rexe)
which we wouldn't want to add to out cases.

Also, we would have to create separate methods for handling the parsing to get
exactly what we require, etc...etc.

The clean way out of this was to have one single data structure. This data
structure will be instantiated whenever a new test case run starts. Hence
every test case run has its own volds ( from hereon, the data structure will be
referred to as volds ).

## Where is volds created.

volds is instantiated when a mixin mixn object is created by a test case run.
If anyone wants to take a peek at how it looks like -> [Mixin](../../common/mixin.py)

## Structure of volds.

Let's look at the set of requirements to better understand why volds is the way
it is.

1. Every volume created by a test case needs to be tracked, hence information
about that volume must be part of the volds. Let's say the name of the volume.
2. What is the type of volume ? This can be discerned by certain parameters
such as replication count, arbiter count, etc. 
3. Building on pt. 1, the second level of information we'd require is which
all servers were used to create this volume and also the bricks coming under
this volume.
4. The next level information is about the mountpoints. Now, there might be
multiple clients, and even in a single client, one can mount at multiple paths,
 hence clients and mountpoints under them.
5. We would also require information regarding the volume options which are
set by the test case ( do we ? If you feel there is a better way, let's discuss
in github discussions :D )

With all these information, one can derive at a guess that volds would be a
dictionary and the approximate form similar to what the actual format is..

```javascript
{
  "volname" : {
                "voltype" : {
                              "replica_count" : q,
                              "dist_count" : r,
                              "arbiter_count" : x,
                              "disperse_count" : y,
                              "redundancy_count" : z
                            },
                "options" : {
                              "option-1" : "value",
                              "option-2" : "value",
                              ...
                              "option-n" : "value"
                            },
                "brickdata" : {
                                "node-1" : ["brickpath1", "brickpath2"],
                                "node-2" : ["brickpath3", "brickpath4"],
                                ...
                                "node-n" : ["brickpathn"]
                              },
                "mountpath" : {
                                "node-1" : ["mnt-path1", "mnt-path2"],
                                ...
                                "node-n" : ["mnt-pathn"]
                              },
                "started" : True/False
              }
}
```

## Methods to get and set data related to volds
TODO: Will be updated once the methods are merged.
