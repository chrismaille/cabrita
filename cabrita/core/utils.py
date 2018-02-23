"""Utils module."""
import os
import sys
import yaml
import re
import subprocess
from buzio import console


def get_yaml(path, file):
    """Open yaml file."""
    try:
        dcfile = os.path.join(path, file)
        with open(dcfile, 'r') as file:
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


def run_command(
        task,
        get_stdout=False,
        run_stdout=False):
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
    except BaseException:
        return False

    return True if not get_stdout else ret.decode('utf-8')


def get_path(path, base_path):
    """Return real path from string.

    Converts environment variables to path
    Converts relative path to full path
    """
    if "$" in path:
        s = re.search("\${(\w+)}", path)
        if not s:
            s = re.search("(\$\w+)", path)
        if s:
            env = s.group(1).replace("$", "")
            name = os.environ.get(env)
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
