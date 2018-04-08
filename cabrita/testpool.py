import random
from multiprocessing import Process
from multiprocessing.pool import Pool
from threading import Thread
from time import sleep


class BoxTest():

    def __init__(self):
        self.result = "1 "
        self.updating = False

    @property
    def can_update(self):
        return not self.updating

    @property
    def status(self):
        return self.result

    def inspect(self):
        sleep(3)
        return str(random.randint(1, 10))


b = BoxTest()


b.updating = False
while True:
    if not b.updating:
        b.updating = True
        with Pool() as pool:
            res = pool.apply_async(b.inspect)
            if res.get():
                b.result = res.get()
                b.updating = False
    print(b.status, end="")
