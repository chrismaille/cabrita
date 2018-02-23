"""Version package.

Checks version number for upgrades in PyPI
"""
import requests
import sys
from buzio import console
from pkg_resources import parse_version
from cabrita import __version__


def versions():
    """Function: versions.

    Summary: Request all versions registered in PyPI
    Returns: list
    """
    console.info("Checking for updates...")
    url = "https://pypi.python.org/pypi/cabrita/json"
    data = None
    versions = None
    try:
        ret = requests.get(url, timeout=1)
        data = ret.json()
    except BaseException:
        pass
    if data:
        versions = list(data["releases"].keys())
        versions.sort(key=parse_version)
    return versions


def check_version():
    """Function: check_version.

    Summary: Compares actual version vs last known
    version in PyPI for upgrades
    Returns: Bool = true if updated
    """
    last_version = __version__
    version_data = versions()
    if version_data:
        last_version = version_data[-1]
    if parse_version(last_version) > parse_version(__version__) and \
            ("rc" not in last_version and
                "b" not in last_version and "dev" not in last_version):
        console.warning(
            "You're running a outdated version.\n" +
            "Last Version: {}\n".format(last_version)
        )
        ret = console.confirm("Do you want to upgrade?")
        if ret:
            result = console.run("sudo pip3 install -U cabrita")
            if result:
                console.success("\nOperation complete. Please run again.")
            else:
                console.error("\nThere is a error during upgrade. Please try again.")
            sys.exit(0)
