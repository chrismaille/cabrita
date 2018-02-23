"""Yaml Parser Module."""
import yaml
import sys
from buzio import console
import os


class Config():
    """Configuration Class.

    Get and parse config from yaml configuration file
    defined in CABRITA_PATH environment settings or
    passed as parameter during initialization.
    """

    def get_file(self, path):
        """Convert configuration yaml file to python dict."""
        try:
            with open(path, 'r') as file:
                data = yaml.load(file.read())
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
            with open(path, 'w') as file:
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
        return os.path.isfile(path)
