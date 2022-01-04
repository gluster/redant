# Code Considerations

## Test Runner Logic

On going through the [test_runner](../core/test_runner.py) or [runner_thread](../core/runner_thread.py), one might think as to why did we use the a list to store a single value in the `testStats[testResult]` variable?
The reason for doing so is based on how python works and the mutable nature of list object in python. Since, we don't have pointers in python we use the mutable nature of lists to modify the values of list by reference and use it across the functions. For reference, one can checkout this article on [pointers-in-python](https://unix.stackexchange.com/questions/321697/why-is-looping-over-finds-output-bad-practice)


## Creating new bricks for volume

In redant, the bricks for a volume are randomly assigned after calculating the unused servers and unused bricks in the cluster, such that the most optimal volume is created (when the volume is created by the framework). If all the bricks have been used up, then it starts from the beginning of the brick_roots (check config file for details) dictionary. Add/Replace/New Bricks follow the same naming structure i.e, `brick/volume_name-brick_number`.
