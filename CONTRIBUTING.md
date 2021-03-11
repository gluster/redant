## Pre-requisites.
1. Github account ( Naturally :p )
2. A little understanding of glusterfs is appreciated as it would come handy while dealing with the TCs and library ops.

## Steps to contribute.

One time effort -
1. Fork the repository.
2. Clone it in your local system.
3. Add an upstream remote to fetch latest changes. `git remote add upstream git@github.com:srijan-sivakumar/redant.git`
4. Fetch the latest changes. `git fetch upstream`.
5. Rebase it to the local clone. `git rebase upstream/main`

Now, step 1-3 once done need not be repeated more than once as once they're done, you can just execute the fetch and rebase command to update your local with
remote upstream. [ Don't forget to update your forked upstream with these latest changes in the `main` ]

The following steps are to be done every time a new PR is being acted upon.
1. Open an issue ( Bug or feature request ) detailing what is expected. Say the issue number is `XYZ`.
2. Run steps 4-5 mentioned in the One time effort.
3. Checkout to a new branch for making changes. `git checkout -b issueXYZ origin/main`
4. Do the changes.
5. Add the changed files before commit. `git add <path-to-file(s)>`
6. Sign your commits with `git commit -s`. This will open an editor. Add the header/subject ( A one liner which will be the header for the PR )
followed by what was changed and why. Also add the line `Updates: #XYZ` or `Fixes: #XYZ` depending on whether this PR will fix an issue raised or
just update a long running issue.
7. Push the changes by running. `git push origin HEAD`

Now, once the PR is opened, tag the reviewers and if the PR requires new changes follow the below steps,
1. Fetch and rebase the local main.
2. Checkout to the issue branch and rebase it to main. `git rebase origin/main`
3. Do the requested changes based on review comments.
4. This time create a new commit by signing the additions. `git commit -s`. and if it is a small change, just run `git commit -s -m '<commit-msg>`.
5. Like the previous steps as followed for the first commit in a PR, add a basic description as to what is changed in this commit and add
`Updates: #XYZ`
6. Push the change. `git push origin HEAD`.

Some prosaic rules,
1. Atleast one vote is required to merge the PR.
2. If there would be multiple changes to a PR, open it as a draft and activate it only when it is ready.
3. Do address the review comments.
4. Try as much as possible to not use the force push.
5. Conscious languages to be followed. Let's be polite :)
6. Contribution can also be done in terms of reviews, just keep point 5 in mind and also that it is the patch and not the person :p
8. Have fun while coding...
