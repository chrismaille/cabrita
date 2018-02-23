"""Cabrita main module."""
import click
from cabrita import __version__
from buzio import console
from cabrita.core.parser import Config
from cabrita.dash import Dashboard
from cabrita.versions import check_version


@click.command()
@click.option(
    '--path',
    envvar="CABRITA_PATH",
    prompt='Inform full path to config file',
    help='Full path for configuration file.',
    type=click.Path())
def run(path):
    """Run main command for cabrita.

    1. Check version
    2. Import configuration file
    3. Run dashboard.
    """
    console.box("Cabrita v{}".format(__version__))
    check_version()
    console.info("Loading Configuration...")
    config = Config().get_file(path)
    dash = Dashboard(config)
    console.info("Reading data...")
    dash.run()


if __name__ == "__main__":
    run()
