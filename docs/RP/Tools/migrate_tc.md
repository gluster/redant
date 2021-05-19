# migrate_tc

This python script was envisaged to pluck test cases from the glusto-tests and
place it on the redant repository and while doing so, also copy the patch
details available in the said file.

The operational logic of the said tool is straightforward. On the availability
of two parameters,
1. Path of the test case to be migrated.
2. Where to be migrated ( directory, and in our case Redant dir )

the tools copies the `.patch` files specific to the said file into a temporary
location ( for us that'd be /tmp ) and then takes it into the redant. To speak
of extra packages required for this tool, as this uses most of the standard
modules in python, this can actually be used in other projects too in future.
