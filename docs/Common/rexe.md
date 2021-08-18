# Remote Execution ( Rexe )

Redant is a test automation framework for a distributed file system and hence
it needs to work with multiple nodes, which implies, connecting to nodes
remotely, requesting some operation from those servers and obtaining the
result. Along the way, it should also handle the re-connection on disconnect
and other exceptions.
