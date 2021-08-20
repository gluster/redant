# What is Redant ?

## Let's start at the beginning...

To understand what is redant and as to why it is required, one needs to
understand as to were we as humans are moving towards. Yeah..Automation..
same old..same old. Reducing the burden and the mundane work which certain
computes can handle without any hesitation.

Every platform, application and product would require some level of testing.
In core engineering fields, there are multiple types of testing which are
performed before an article or item is certified to be fit to use.

Continuing in that same line of thought, to be certified or verified that a 
piece of software is good enough to be used without causing serious damage
or disruption, we need to perform testing. If one looks into this from a very
high level view, they can see a loop, testing finds bugs and issues in the
software and then we add new features or fix the existing issues which can
still cause more issues.

The said issues can be either functional or performance based. It might be that
there are no functional issues with the product but what's the use of the 
product itself if it doesn't deliver the required operation within a said time
limit with expected speed.

One important aspect of testing is the environemnt. One can see happy scenarios
when running a code in a very big plush server overflowing with memory but
the same piece of code might not even run in an edge device because of the
space constraints. Similarly even the performance will change.

## Still not impressed ?

With increasing penetration of digital technology around the world, data would
be of essence, and the prosaic part of it is storage. Storage is the bed rock
or the tabla rosa on which everything resides. Kernel code runs in the storage
space provided to give some utility and the same is true for any popular,
unpopular and unknown piece of software. This would then mean that a slight 
disruption in retrieval of data or even a reduction in the performance of 
storage solution would translate to m(b)illions of tokens ( or currency ). 

Hence before the product is shipped, it needs to be tested. We need to make
sure that any potential operation performed by user doesn't tank the software.
This not only means verifying the said features but also breaking it deliberately.
And then documenting that if something of this sort is done, this is what will
happen.

The question now is not why we need to test but to how...

## Ok..time to loop it all together

Now imagine a person manually testing a piece of software. Every detail, every
environmental parameter, metric etc has to be taken care of and accounted for.
You miss one factor and the results would vary and inferences will vary.

This begs the question...do we have a better way ?

We always do.

Replace humans with a piece of software which won't require the coffee breaks,
lunchtimes, PTOs and sick leaves. They'd just humm along and do what they are 
told to. But they have a limitaiton. Computes are good at automating repetivite
task ( Now this is changing but not in scope our discussion here :p), or
remembering multiple things, but they lack the foresight of how a human might
use a piece of software ( Again..shifting times...still rolling with it ).

So here we are, humans telling computes how to test a piece of instruction.

To reach this point where we are, we had to go through lot of design decisions
and moments when our laptops would have fallen out of the window ( Kidding ! ).
And that means thought process put into every inch of how this framework will
behave. How a certain component will behave and interact with another component.
Even anticipating user requirements ( Maybe we should say assuming ) and 
working accordingly.

This is what Redant is at the end of the day, amalgamation of thought process
of multiple people from around the world. A test automation framework for a 
distributed file system and anybody who wants to learn and understand how the
engine humms, has to peer into these docs to understand why it is so.

## All right, let's get to more technical parts from now on...

We solemly swear that there is no more essays on history, computes and other things
unless and until required.

Continuing ahead one can go over to the [High Level Design](./HLD.md)
