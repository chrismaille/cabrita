"""Yaml Parser Module."""
import yaml
import sys
from buzio import console


class Config():
    """Configuration Class.

    Get and parse config from yaml configuration file
    defined in CABRITA_PATH environment settings or
    passed as parameter during initialization.
    """

    def __init__(self, path):
        """Init Class."""
        self.path = path

    def get_config(self):
        """Convert configuration yaml file to python dict."""
        try:
            with open(self.path, 'r') as file:
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
