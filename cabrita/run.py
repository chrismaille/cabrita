"""Cabrita.

Usage:
  cabrita dash -d <path>
  cabrita -h | --help
  cabrita --version

Options:
  -h --help     Show this screen.
  --version     Show version.
"""
from cabrita import __version__
from buzio import console
from docopt import docopt
from cabrita.docker import Dashboard


def run():
    console.box("Cabrita v{}".format(__version__))
    arguments = docopt(__doc__, version=__version__)
    if arguments['dash']:
        dash = Dashboard(arguments['<path>'])
        dash.run()


if __name__ == "__main__":
    run()
