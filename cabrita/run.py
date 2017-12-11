"""Cabrita.

Usage:
  cabrita dash [--path=<path>] [--config=<config>]
  cabrita -h | --help
  cabrita --version

Options:
  -h --help     Show this screen.
  --version     Show version.
"""
import os
import yaml
import sys
from cabrita import __version__
from buzio import console
from docopt import docopt
from cabrita.commands import Dashboard
from cabrita.versions import check_version

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_configuration(path=None):
    config_file = os.path.join(path, 'cabrita.yml')
    try:
        with open(config_file, 'r') as file:
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


def run():
    console.box("Cabrita v{}".format(__version__))
    arguments = docopt(__doc__, version=__version__)
    check_version()
    if arguments['--config']:
        path = arguments['--config']
    else:
        path = BASE_DIR
    config = get_configuration(path)
    if arguments['dash']:
        dash = Dashboard(arguments['--path'], config)
        dash.run()


if __name__ == "__main__":
    run()
