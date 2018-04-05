import os
import yaml
import sys
from abc import ABC, abstractmethod
from cabrita.abc.utils import run_command
from buzio import console, formatStr
from datetime import datetime, timedelta

from cabrita.abc.utils import get_path


class ConfigTemplate(ABC):

    def __init__(self):

        self.base_path = os.getcwd()
        self.list_path = []
        self.full_path = None
        self.data = {}
        self.console = console


    @property
    def version(self):
        return self.data['version']

    @property
    @abstractmethod
    def is_valid(self) -> bool:
        pass

    def add_path(self, path):
        self.list_path.append(path)


    def load_data(self):
        for path in self.list_path:
            try:
                self.full_path = get_path(path, self.base_path)
                self.console.info("Reading {}".format(path))
                with open(self.full_path, 'r') as file:
                    data_from_file = yaml.load(file.read())
                    self.data = self.data.update(data_from_file)
            except IOError as exc:
                console.error("Cannot open file: {}".format(exc))
                sys.exit(1)
            except yaml.YAMLError as exc:
                console.error("Cannot read file: {}".format(exc))
                sys.exit(1)
            except Exception as exc:
                console.error("Error: {}".format(exc))
                raise exc


class InspectTemplate(ABC):

    def __init__(self, compose, interval: int):

        self.base_path = os.getcwd()
        self.run = run_command
        self.compose = compose
        self._status = formatStr.info("Fetching...", theme="dark", use_prefix=False)
        self.interval = interval
        self.last_update = datetime.now() - timedelta(seconds=self.interval)
        self.path = None


    @abstractmethod
    def inspect(self, service: str):
        pass

    @property
    def can_update(self) -> bool:
        seconds_elapsed = (datetime.now() - self.last_update).total_seconds()
        return seconds_elapsed >= self.interval

    def status(self, service):
        if self.can_update:
            self.inspect_all()
        return self._status[service]

    def inspect_all(self):
        for service in self.compose.services:
            self._status[service] = self.inspect(service)
        self.last_update = datetime.now()