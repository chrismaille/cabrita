"""Base utils module.

Functions
---------
    get_sentry_client: Return Sentry client
    run_command: Run subprocess calls
    get_path: Resolve relative paths
    format_color: Abstract buzio formatStr method

"""
import os
import re
import subprocess
from typing import Union, Optional

from buzio import formatStr
from raven import Client
from raven.transport.requests import RequestsHTTPTransport


def get_sentry_client() -> Optional[Client]:
    """Return synchronous Sentry client if DSN is available."""
    return Client(os.getenv('CABRITA_SENTRY_DSN'), transport=RequestsHTTPTransport) if os.getenv(
        'CABRITA_SENTRY_DSN') else None


def run_command(
        task,
        get_stdout=False,
        run_stdout=False) -> Union[str, bool, KeyboardInterrupt]:
    """Run subprocess command.

    Args:
        task (string): the command to run
        get_stdout (bool, optional): capture stdout
        run_stdout (bool, optional): capture and run stdout

    Returns:
        Bool or String: Bool if task was executed or stdout
    """
    try:
        if run_stdout:
            command = subprocess.check_output(task, shell=True)

            if not command:
                return False

            ret = subprocess.call(command, shell=True)

        elif get_stdout is True:
            ret = subprocess.check_output(task, shell=True)
        else:
            ret = subprocess.call(
                task,
                shell=True,
                stderr=subprocess.STDOUT
            )

        if ret != 0 and not get_stdout:
            return False
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception:
        return False

    return True if not get_stdout else ret.decode('utf-8')


def get_path(path: str, base_path: str) -> Union[str, ValueError]:
    """Return real path from string.

    Converts environment variables to path
    Converts relative path to full path
    """
    if "$" in path:
        s = re.search(r"\${(\w+)}", path)
        if not s:
            s = re.search(r"(\$\w+)", path)
        if s:
            env = s.group(1).replace("$", "")
            name = os.environ.get(env)
            if not name:
                raise ValueError("Can't find value for {}".format(env))
            path_list = [
                part if "$" not in part else name
                for part in path.split("/")
            ]
            path = os.path.join(*path_list)
        else:
            raise ValueError(
                "Cant find path for {}".format(path)
            )
    if path.startswith("."):
        list_path = os.path.join(base_path, path)
        path = os.path.abspath(list_path)
    return path


def format_color(text: str, style: str, theme: str = None) -> str:
    """Format string with color using formatStr method."""
    func = getattr(formatStr, style)
    return func(text, use_prefix=False, theme=theme) if theme else func(text, use_prefix=False)
