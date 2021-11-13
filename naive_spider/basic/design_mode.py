class Singleton:
    '''
    The base class which makes it and its subclasses all are singletons.
    Usage:
        class A(Single):
            pass
    '''
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance