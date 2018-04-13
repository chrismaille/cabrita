"""Cabrita main module."""
import sys

import backtrace
import click
from cabrita import __version__
from buzio import console

from cabrita.abc.utils import get_sentry_client
from cabrita.command import DashboardCommand
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
    try:
        print("")
        console.box("Cabrita v{}".format(__version__))
        version = check_version()
        console.info("Loading Configuration...")
        dashboard = DashboardCommand()
        dashboard.add_config(path)
        if not dashboard.config.is_valid:
            sys.exit(1)
        dashboard.add_compose()
        dashboard.add_version(version)
        if dashboard.compose.is_valid:
            console.success('Configuration complete. Starting dashboard...')
            dashboard.execute()
        else:
            sys.exit(1)
    except Exception:
        client = get_sentry_client()
        if client:
            client.captureException()

        backtrace.hook(
            reverse=False,
            align=True
        )
        raise



if __name__ == "__main__":
    run()
