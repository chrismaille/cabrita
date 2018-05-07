import os
import sys
from abc import ABC, abstractmethod
from collections import Hashable
from datetime import datetime, timedelta
from typing import Union, Dict, List, Any

import yaml
from buzio import console

from cabrita.abc.utils import get_path
from cabrita.abc.utils import run_command


class ConfigTemplate(ABC):
    """
    Abstract class for processing yaml files.
    """
    compose_data = Union[Union[Dict[Hashable, Any], List[Any], None], Any]

    def __init__(self) -> None:
        self.compose_data_list = []
        self._base_path = None
        self.list_path = []
        self.full_path = None
        self.data = {}
        self.console = console
        self.manual_compose_paths = []

    @property
    def base_path(self):
        return self._base_path

    @base_path.setter
    def base_path(self, value):
        self._base_path = value if "$" not in value else get_path(value, "")

    @property
    def version(self) -> int:
        return int(self.data.get("version", 0))

    @property
    @abstractmethod
    def is_valid(self) -> bool:
        pass

    def add_path(self, path: str, base_path: str = os.getcwd()) -> None:
        if path:
            if not self.base_path:
                self.base_path = base_path
            self.list_path.append((path, base_path))

    def load_data(self) -> None:
        if self.list_path:
            for path, base_path in self.list_path:
                try:
                    self.full_path = get_path(path, base_path)
                    self.console.info("Reading {}".format(self.full_path))
                    with open(self.full_path, 'r') as file:
                        self.compose_data = yaml.load(file.read())
                        for key in self.compose_data:
                            self._convert_lists(self.compose_data, key)
                        self.compose_data_list.append(self.compose_data)
                except IOError as exc:
                    console.error("Cannot open file: {}".format(exc))
                    sys.exit(1)
                except yaml.YAMLError as exc:
                    console.error("Cannot read file: {}".format(exc))
                    sys.exit(1)
                except Exception as exc:
                    console.error("Error: {}".format(exc))
                    raise exc
            self._upload_compose_list()

    def _convert_lists(self, data, key):
        if isinstance(data[key], list) and "=" in data[key][0]:
            data[key] = {obj.split("=")[0]: obj.split("=")[-1] for obj in data[key]}
        if isinstance(data[key], dict):
            for k in data[key]:
                self._convert_lists(data[key], k)

    def _upload_compose_list(self):
        reversed_list = list(reversed(self.compose_data_list))
        self.data = reversed_list[-1]
        for index, override in enumerate(reversed_list):
            self.override = override
            if index + 1 == len(reversed_list):
                break
            for key in self.override:
                self._load_data_from_override(self.override, self.data, key)

    def _load_data_from_override(self, source, target, key):
        """Append override data in self.compose.

            Example Compose
            ---------------
            core:
                build:
                    context: ../core
                image: core
                networks:
                    - backend
                environment:
                    - DEBUG=false
                ports:
                 - "8080:80"

            Example override
            ----------------
            core:
                build:
                    dockerfile: Docker_dev
                depends_on:
                    - api
                command: bash -c "python manage.py runserver 0.0.0.0"
                environment:
                    DEBUG: "True"
                ports:
                    - "9000:80"

            Final Result
            ------------
            core:
                build:
                    context: ../core
                    dockerfile: Docker_dev
                depends_on:
                    - api
                image: core
                command: bash -c "python manage.py runserver 0.0.0.0"
                environment:
                    DEBUG: "True"
                networks:
                    - backend
                ports:
                 - "8080:80"
                 - "9000:80"

        """
        if target.get(key, None):
            if isinstance(source[key], dict):
                for k in source[key]:
                    self._load_data_from_override(
                        source=source[key],
                        target=target[key],
                        key=k
                    )
            else:
                if isinstance(target[key], list) and isinstance(source[key], list):
                    target[key] += source[key]
                else:
                    target[key] = source[key]
        else:
            if isinstance(target, list) and isinstance(source[key], list):
                target[key] += source[key]
            else:
                target[key] = source[key]


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
        self.path = None
        self.default_data = None

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

        return self._status.get(service, self.default_data)
