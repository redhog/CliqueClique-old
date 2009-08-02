import threading

class ThreadsafeConnection(object):
    def __init__(self, connection_factory):
        class Local(threading.local):
            factory = [connection_factory]
            def __init__(self):
                self.conn = self.factory[0]() # Not a method!
        object.__setattr__(self, "_local", Local())

    def __hasattr__(self, name):
        return hasattr(object.__getattribute__(self, "_local").conn, name)

    def __getattribute__(self, name):
        return getattr(object.__getattribute__(self, "_local").conn, name)

    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, "_local").conn, name, value)
