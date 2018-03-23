"""Cabrita main module."""
import click
from cabrita import __version__
from buzio import console
from cabrita.versions import check_version
from cabrita.components.config import Config
from cabrita.components.compose import Compose
from cabrita.components.dashboard import Dashboard

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

    dashboard = Dashboard()

    console.info("Loading Configuration...")
    dashboard.config = Config(path)
    dashboard.config.load_data()
    if not dashboard.config.is_valid:
        console.error("Please check errors before continue")
        sys.exit(1)

    console.info("Reading data from docker-compose...")
    dashboard.compose = Compose()
    dashboard.compose.load_data()
    if not dashboard.compose.is_valid:
        console.error("Please check errors before continue")
        sys.exit(1)

    console.info("Starting dashboard...")
    dashboard.run()


if __name__ == "__main__":
    run()
