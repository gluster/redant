class test_class:

    def __init__(self, remote_exec):
        self.remote_exec = remote_exec

    @classmethod
    def test_fn(cls):
        print("Hello world!")
