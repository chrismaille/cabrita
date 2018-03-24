from datetime import datetime
from threading import Thread

class Box(Thread):


    def __init__(self):

        self._widget = ""
        self.last_update = datetime.now()
        self.interval = 0
        self.data = {}

    @property
    def can_update(self) -> bool:
        seconds_elapsed = (datetime.now() - self.last_update).total_seconds()
        return seconds_elapsed >= self.interval

    @property
    def widget(self):
        if self.can_update:
            self.run()
        return self._widget


    @widget.setter
    def widget(self, value):
        self._widget = value


    def load_data(self, data: dict):
        self.data = data

    def run(self):
        pass



