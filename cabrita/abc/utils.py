import subprocess

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