import os
import yaml
import re
import sys
from abc import ABC, abstractmethod
from typing import List
from buzio import console


def get_path(path, base_path):
    """Return real path from string.

    Converts environment variables to path
    Converts relative path to full path
    """
    if "$" in path:
        s = re.search("\${(\w+)}", path)
        if not s:
            s = re.search("(\$\w+)", path)
        if s:
            env = s.group(1).replace("$", "")
            name = os.environ.get(env)
            path_list = [
                part if "$" not in part else name
                for part in path.split("/")
            ]
            path = os.path.join(*path_list)
        else:
            raise ValueError(
                "Cant find path for {}".format(path)
            )
    if path.startswith("."):
        list_path = os.path.join(base_path, path)
        path = os.path.abspath(list_path)
    return path


class ConfigBase(ABC):

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