import os
from typing import Union

import yaml
import sys
from abc import ABC, abstractmethod
from cabrita.abc.utils import run_command
from buzio import console
from datetime import datetime, timedelta

from cabrita.abc.utils import get_path


class ConfigTemplate(ABC):
    """
    Abstract class for processing yaml files.
    """
    def __init__(self) -> None:
        self.base_path = os.getcwd()
        self.list_path = []
        self.full_path: str = None
        self.data = {}
        self.console = console

    @property
    def version(self) -> str:
        return self.data['version']

    @property
    @abstractmethod
    def is_valid(self) -> bool:
        pass

    def add_path(self, path: str) -> None:
        self.list_path.append(path)

    def load_data(self) -> None:
        for path in self.list_path:
            try:
                self.full_path = get_path(path, self.base_path)
                self.console.info("Reading {}".format(path))
                with open(self.full_path, 'r') as file:
                    data_from_file = yaml.load(file.read())
                    self.data.update(data_from_file)
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
    """
    Abstract class for docker service inspectors.
    """
    def __init__(self, compose: ConfigTemplate, interval: int) -> None:
        self.base_path = os.getcwd()
        self.run = run_command
        self.compose = compose
        self._status = {}
        self.interval = interval
        self.last_update = datetime.now() - timedelta(seconds=self.interval)
        self.path: str = None
        self.default_data: Union[dict, str] = None

    @abstractmethod
    def inspect(self, service: str) -> None:
        pass

    @property
    def can_update(self) -> bool:
        seconds_elapsed = (datetime.now() - self.last_update).total_seconds()
        return seconds_elapsed >= self.interval

    def status(self, service) -> Union[dict, str]:
        """
        Return service status.
        If can update, start fetching new data calling self.inspect method.

        :param service:
            docker service name
        :return:
            dict or string. If not fetch data yet send default data.
        """
        if self.can_update:
            self.inspect(service)
        return self._status[service] if self._status.get(service) else self.default_data
