"""Yaml Parser Module."""
import yaml
import sys
from buzio import console
import os
from cabrita.core.utils import get_path


class Config():
    """Configuration Class.

    Get and parse config from yaml configuration file
    defined in CABRITA_PATH environment settings or
    passed as parameter during initialization.
    """

    def get_file(self, path):
        """Convert configuration yaml file to python dict."""
        try:
            full_path = get_path(path, str(os.getcwd()))
            with open(full_path, 'r') as file:
                data = yaml.load(file.read())
                data['file_path'] = path
            return data
        except IOError as exc:
            console.error("Cannot open file: {}".format(exc))
            sys.exit(1)
        except yaml.YAMLError as exc:
            console.error("Cannot read file: {}".format(exc))
            sys.exit(1)
        except Exception as exc:
            console.error("Error: {}".format(exc))
            sys.exit(1)

    def save_file(self, path, content):
        try:
            full_path = get_path(path, str(os.getcwd()))
            with open(full_path, 'w') as file:
                yaml.dump(content, file)
        except IOError as exc:
            console.error("Cannot open file: {}".format(exc))
            sys.exit(1)
        except yaml.YAMLError as exc:
            console.error("Cannot read file: {}".format(exc))
            sys.exit(1)
        except Exception as exc:
            console.error("Error: {}".format(exc))
            sys.exit(1)

    def check_file(self, path):
        full_path = get_path(path, str(os.getcwd()))
        return os.path.isfile(full_path)
