import os
import sys
import yaml
import subprocess
from buzio import console


def get_yaml(path, file):
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
    """Summary

    Args:
        task (TYPE): Description
        get_stdout (bool, optional): Description
        run_stdout (bool, optional): Description

    Returns:
        TYPE: Description
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
    except BaseException:
        return False

    return True if not get_stdout else ret.decode('utf-8')
