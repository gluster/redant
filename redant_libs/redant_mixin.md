# Redant Mixin

## The why ?

Before going to as to what is a mixin and how it works, we need to address the why.
What was the issue which prompted the use of mixin.

Now if one checks the dependency flow without mixin ( Refer the image below ), it shows
that the Rexe object ( i.e. remote executioner ) was created by the runner thread and then
passed to the test case to be used.

![](https://github.com/srijan-sivakumar/Redant/raw/main/images/without_mixin.jpg)

But we also know that the ops libraries extensively use the rexe and log objects and method.
This implies we have to import those modules into all these ops libraries and then pass the 
object every time the ops functions were invoked. Bit of a duplicate code and PITA ( pardon my french ).

Also, the test cases would have to import each and every module it has to use and if anythin changes
in the framework level, i.e. say a module was combined with another module, then every TC has to be 
changed inline with that.

So duplication of code, passing of extra parameters for each and every call and also the intention
is not to make a global object of rexe, logger and pass it around for fun. Hence, Mixin.

## What is mixin.

 Now, I wouldn't want to go on a complete introduction to design patterns and giving an example
of as to what a mixin does, so for reference, [Wikipedia on Mixin](https://en.wikipedia.org/wiki/Mixin).

## How is mixin being used in Redant.
As we have seen in the why, we have multiple support and ops libraries which are interlinked by some
or the other relation and all of these are then being used by our test cases, so why not use a little
bit of OOP and create a child who imports from all ?

Cool, but what about the interdependency of these support of ops libs ? ( Please refer the wiki link
for understanding how mixin works )

So, this object is instantiated for each and every test case run and hence is specific to a given config. This
is done inside the `runner_thread` which then passes on the reference during the creation of an object of a test
case.

The test cases then only need to use this object to invoke any of the support functions instead of using
multiple different objects for different libraries.

## Adding a new support or ops module.

The following is a sample template for adding a support or ops module inside redant_libs.

```
# Required imports
#

class sample_ops_class:

	def func1():
		self.func2()
		self.func3()

	def func2():
		some_operation

```

Now, one might notice that we haven't defined or declared func3 inside this module. You might wonder that
I would've simply added them in imports but NO! It won't be imported by us. For our sake, let's say that
`func3` is actually defined in a module called `sample_ops2`'s class `sample_op2_class`.

Once the above support library is created, one needs to add the module inside the `redant_mixin` and 
let the `redant_mixin` class inherit from this newly added class.

```
from redant_libs.support_libs.rexe import Rexe
from redant_libs.gluster_libs.sample_ops1 import sample_ops_class # the newly added module
from redant_libs.gluster_libs.sample_ops2 import sample_ops2_class 

class redant_mixin(Rexe, sample_ops_class, sample_ops2_class):
	pass
```

This is the mixin magic. The `redant_mixin` objects would then be able to handle the relation
between the `sample_ops_class` and `sample_ops2_class`. Hence allowing us to pass on this mixin object
to a test case to be used for invocation of all the library calls from the test case without importing
the ops modules inside a TC.
