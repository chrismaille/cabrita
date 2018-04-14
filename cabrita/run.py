"""Cabrita main module."""
import sys

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
    default=None,
    help='Full path for configuration file.',
    type=click.Path())
@click.argument(
    'compose_path',
    type=click.Path(exists=True),
    nargs=-1
)
def run(path, compose_path):
    """Run main command for cabrita.

    1. Check version
    2. Import configuration file
    3. Run dashboard.
    """
    try:
        print("")
        console.box("Cabrita v{}".format(__version__))
        version = check_version()
        if path:
            console.info("Loading Configuration...")
        dashboard = DashboardCommand()
        dashboard.add_config(path, compose_path)
        if not dashboard.config.is_valid:
            sys.exit(1)
        dashboard.add_compose()
        dashboard.add_version(version)
        if dashboard.compose.is_valid:
            console.success('Configuration complete. Starting dashboard...')
            dashboard.execute()
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        client = get_sentry_client()
        if client:
            client.captureException()
        raise



if __name__ == "__main__":
    run()
