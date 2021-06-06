# glusto_redant_parser

The Glusto test cases and the glusto framework itself has been there for years
now and there are around 400+ test cases present in it. Now a manual conversion
of these test cases from glusotish form to redantish form is easy but,
nonetheless annoying. Who would want to work on the document and remove space,
add a line, convert license lines etc etc.

Hence it becomes our responsibility to churn out a new solution or tool to help
those taking on the brave task of test case migration.

Ok, now that we have hashed out the why, let's move on to the how.

## Segments in code.

When starting out with the parsing and conversion, one thing which came to the
mind is how a compiler performs pre-processing. This implied one needs to
identify components in the code which can be easily pointed out or identified
in every test case.

Following were the segments of code which were zeroed into,
1. License section
2. Import lines
3. Runs-on decorator
4. Class

The idea was to break a glusto-test test case code into these four segments,
then individually transform each of these segments to a redantish mode
and finally add them to the test file and let the user run the final stretch
in the conversion.

The straighforward conversions in these were that of the license and the import
lines. Let's take a look into individual segments.

## License section

Glusto adds license information as a combination of multiple single line
comments but in Redant, we use the very first single line comment to determine
the test case nature and the volumes for which it needs to run. This means we 
need to convert these lines from single line to that of a block comment.

## Import lines

We simply ignore the glusto specific imports and only take in non glusto
imports. Also a bare minimum import line for the parent is added.

## Runs-on decorator.

This is where we'd be obtaining the information regarding the volume types
for which this test case needs to be run and hence populate the test case
nature comment in the test case in Redant.

## Class

Glusto specific `self.log*` as well as the `self.assert*` lines are to be
removed as Redant takes a different approach in validating commands. Along with
this the `teardown` and `setup` specific functions are removed. Apart from this
other functions are allowed to continue.

## The final mix

Once all the above segments are transformed, they are combined in the test file
according to the standard structure of the Redant test files.

## What can be done in future ?

Currently we don't transform the ops functions being called in the test case
and this can be done ( ofcourse...it just needs more data and support ), but
for now, we can live with what we have.
