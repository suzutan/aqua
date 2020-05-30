from threading import Lock


class Singleton:
    __instance = None
    __lock = Lock()

    def __new__(cls, *args, **kwargs):
        cls.__lock.acquire()
        if cls.__instance is None:
            cls.__instance = super(Singleton, cls).__new__(cls)
        cls.__lock.release()
        return cls.__instance
