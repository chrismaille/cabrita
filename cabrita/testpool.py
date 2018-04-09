import random
from multiprocessing import Process, Queue
from multiprocessing.pool import Pool
from threading import Thread
from time import sleep


class BoxTest():

    def __init__(self):
        self.code = "a"
        self.result = "1 "
        self.updating = False

    @property
    def can_update(self):
        return True

    @property
    def status(self):
        return self.result

    def inspect(self):
        sleep(3)
        self.result = "{}{} ".format(self.code, random.randint(1, 10))

q = Queue()
b = BoxTest()



while True:
    p = Process(target=b.inspect)
    p.start()
    p.join()
    print(b.status, end="")
