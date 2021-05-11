# Migrating Test cases from Gluto-tests to Redant

It is no secret that a huge amount of effort went into the creation and
addition of test cases to Glusto-tests. To quote Newton, we all stand on the
shoulders of giants and hence, instead of re-creating everything from scratch
we decided long back to re-use and modify the test cases.

Now that doesn't mean that we just copy the said test cases and be done with
it..NO, we are supposed to guard the commit history of every test case we
migrate. The reason being we need to show the requisite kudos to people
who have worked on those test cases and to those who had come up with the
test scenarios.

It will be a little extra step, but that extra step is what defines an open
source idealogy.

## Cool, but what needs to be done ?

The very first step would be to fork both the redant and glusto-test repos.
For those who don't know where to find glusto-tests, the repository lives at
[glusto-tests](https://github.com/gluster/glusto-tests).

Once the repository has been forked, clone it to your local machine where you'd
be performing the migration.

```
# git clone git@github.com:<username>/redant.git
# git clone git@github.com:<username>/glusto-tests.git
```

Add a remote in case of redant repository so as to rebase in future if need be.

```
# git remote add upstream git@github.com:srijan-sivakumar/redant.git
```

The next step would be to determining which test case you'd be migrating. The
best practice would be to create an issue in Redant for migration clearly
stating which test case would be migrated, so as to avoid confusion.

Post that, create a new branch in the local repository of redant,

```
# git checkout -b issue<issueID> origin/main
```

The nex batch of steps are important and the explanation of what is happening
is not provided in this markdown. For the ever curious souls, we'd add a blog
post in future to explain what gears are turning for these given set of git
commands.

1. Create a temporary directory wherein we would be storing the .patch files
from our source repo ( glusto-tests ) to destination repo ( redant ). For
instance, lets say at tmp directory.

```
# mkdir -p /tmp/issue<issueID>
```

2. Navigate to the source repo ( glusto-tests ) directory which we have already
cloned in our local machine.

```
# cd <somepath>/glusto-tests
```

3. Export a environment variable which contains the path of the file with 
the source repo ( i.e. glusto-tests ) as the base dir. For example, if you
were migrating a test file `test_glusterd_sample.py` residing inside the 
directory, `<somepath>/glusto-tests/tests/functional/glusterd/`, then the
path we should give to the environement variable is 
`tests/functional/glusterd/test_glusterd_sample.py`.

```
# export reposrc=tests/functional/glusterd/test_glusterd_sample.py
```

One just needs to replace the path with the path of the test case they're
migrating.

4. In this step, to give a very simple explanation, we'd be using the exported
path variable to find the `.patch` files for the said files and copy it to the
directory we had created inside /tmp.

```
# git format-patch -o /tmp/issue<issueID> $(git log $reposrc| grep ^commit|tail -1|awk '{print $2}')^..HEAD $reposrc
```

5. Switch to the desitnation directory ( redant ) which we have already cloned,

```
# cd <somepath>/redant
```

6. The Next step would be to use the `git am` and the list of patches for a
file which we have copied to the `/tmp` directory and use that on the 
destination repository.

```
# git am /tmp/issue<issueID>/*.patch
```

7. If one were to see the current commit in the git log, they'd find the set
of patches belonging to the file we had transferred. Hence the first half of
the migraiton is complete.

8. The second half of the migration. Well..herein you'd have to work a little
more, read the existing docs on redant to see how a test case is to be 
formatted, what imports to be done, removing assertions and logs, etc etc.
If any ops is required to run the said test case, take that as part of this
patch. 

9. Once you're done with the changes, just run the tests, fix the linting 
issues and push the code for review. Sit back and have the beverage of your
choice till the review is done. Once the patch has been merged, we'd see that
all the people who've worked on the said patches would now be shown as 
contributor to the project and also, we would retain the commit history.

If there are issues with the said set of commands, or any doubts, do raise
an issue or better let's discuss at Discussions and if need be we'll open
an issue to fix things.
