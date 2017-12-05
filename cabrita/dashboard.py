"""Cabrita.

Usage:
  cabrita -f <path>
  cabrita -h | --help
  cabrita --version

Options:
  -h --help     Show this screen.
  --version     Show version.

Attributes:
    arguments (TYPE): Description
    dc_path (TYPE): Description
"""
import os
import psutil
import re
import subprocess
import sys
import yaml
from asciimatics.event import KeyboardEvent
from asciimatics.exceptions import ResizeScreenError, StopApplication
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.widgets import Frame, Layout, MultiColumnListBox, Widget, Label, TextBox
from buzio import console
from collections import defaultdict
from docopt import docopt
from git import Repo


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


class StatusFrame(Frame):

    """Summary

    Attributes:
        dc_path (TYPE): Description
        palette (TYPE): Description
        repo (TYPE): Description
        service (TYPE): Description
    """

    def __init__(self, screen):
        """Summary

        Args:
            screen (TYPE): Description
        """
        super(StatusFrame, self).__init__(screen,
                                          screen.height,
                                          screen.width,
                                          has_border=False,
                                          name="My Form")
        # Internal state required for doing periodic updates
        self._last_frame = 0
        self._sort = 5
        self._reverse = True
        self.dc_path = DOCKER_COMPOSE_PATH

        # Create the basic form layout...
        layout = Layout([1], fill_frame=True)
        self._header = TextBox(1, as_string=True)
        self._header.disabled = True
        self._header.custom_colour = "label"
        self._services = TextBox(1, as_string=True)
        self._services.custom_colour = "label"
        self._services.disabled = True
        self._list = MultiColumnListBox(
            Widget.FILL_FRAME,
            [16, 24, 20, 10, 10, 10, 10, "100%"],
            [],
            titles=["Project", "Branch", "Git", "Server", "Worker", "Beat", "Flower", "Redis"],
            name="mc_list")
        self.add_layout(layout)
        layout.add_widget(self._header)
        layout.add_widget(self._services)
        layout.add_widget(self._list)
        ret = run_command(
            "cd {} && git status -bs --porcelain".format(DOCKER_COMPOSE_DIR),
            get_stdout=True
        )
        if "ahead" in ret:
            text = "YOUR DOCKER-COMPOSE FILE IS OUTDATED. Please update."
        else:
            text = "File {} is up-to-date.".format(self.dc_path)
        layout.add_widget(
            Label("{}. Press `q` to quit.".format(text))
        )
        self.fix()

        # Add my own colour palette
        self.palette = defaultdict(
            lambda: (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK))
        for key in ["selected_focus_field", "label"]:
            self.palette[key] = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK)
        self.palette["title"] = (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE)

    def process_event(self, event):
        """Summary

        Args:
            event (TYPE): Description

        Returns:
            TYPE: Description

        Raises:
            StopApplication: Description
        """
        # Do the key handling for this Frame.
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord('q'), ord('Q'), Screen.ctrl("c")]:
                raise StopApplication("User quit")

            # Force a refresh for improved responsiveness
            self._last_frame = 0

        # Now pass on to lower levels for normal handling of the event.
        return super(StatusFrame, self).process_event(event)

    def get_branch(self, name):
        """Summary

        Args:
            name (TYPE): Description

        Returns:
            TYPE: Description
        """
        if COMPOSE_DATA['services'][name].get('build'):
            data = COMPOSE_DATA['services'][name]['build']['context']
            s = re.search(r"\w+", data)
            if s:
                env = s.group(0)
                path = os.environ.get(env)
                self.repo = Repo(path)
                text = self.repo.active_branch.name
            else:
                text = data
        else:
            text = "Using Image"
        return text

    def get_git_status(self):
        """Summary

        Returns:
            TYPE: Description
        """
        text = "--"
        if self.repo.is_dirty():
            text = "Modified"
        ret = run_command(
            "cd {} && git status -bs --porcelain".format(self.repo.working_dir),
            get_stdout=True
        )
        if "behind" in ret:
            text = "Need to Pull"
        elif "ahead" in ret:
            text = "Need to Push"
        return text

    def check_server(self, name, service_type):
        """Summary

        Args:
            name (TYPE): Description
            service_type (TYPE): Description

        Returns:
            TYPE: Description
        """
        if service_type != "server":
            full_name = "{}-{}".format(name, service_type)
        else:
            full_name = name
        found = [
            k
            for k in COMPOSE_DATA['services']
            if k == full_name
        ]
        if not found:
            text = ""
        else:
            ret = run_command(
                'docker ps | grep "{0}$\|{0}_run"'.format(full_name),
                get_stdout=True
            )
            if ret:
                text = "Running"
            else:
                text = "--"
        return text

    def _update(self, frame_no):
        """Summary

        Args:
            frame_no (TYPE): Description
        """
        # Refresh the list view if needed
        if frame_no - self._last_frame >= self.frame_update_count or self._last_frame == 0:
            self._last_frame = frame_no

            # Create the data to go in the multi-column list...
            last_selection = self._list.value
            last_start = self._list.start_line
            list_data = []
            for key in COMPOSE_DATA['services']:
                self.service = COMPOSE_DATA['services'][key]
                service_type = "".join(key.split("-")[-1])
                if service_type.lower() in ['worker', 'beat', 'flower', 'redis'] \
                        and key != "banks-worker":
                    continue
                if key in ['postgres', 'mongodb', 'migrate', 'memcache', 'traefik', 'geru-ngrok', 'geru-ftp']:
                    continue
                if key.startswith("sentry"):
                    continue
                name = "".join(key.split("-")[0])
                data = [
                    key,
                    self.get_branch(key),
                    self.get_git_status(),
                    self.check_server(key, "server"),
                    self.check_server(name, "worker"),
                    self.check_server(name, "beat"),
                    self.check_server(name, "flower"),
                    self.check_server(name, "redis"),
                ]
                list_data.append(data)

            new_data = [
                ([
                    x[0],
                    x[1],
                    x[2],
                    x[3],
                    x[4],
                    x[5],
                    x[6],
                    x[7]
                ], x[0]) for x in list_data
            ]

            # Update the list and try to reset the last selection.
            self._list.options = new_data
            self._list.value = last_selection
            self._list.start_line = last_start
            self._header.value = (
                "CPU usage: {}%   Memory available: {}M".format(
                    str(round(psutil.cpu_percent() * 10, 0) / 10),
                    str(int(psutil.virtual_memory().available / 1024 / 1024))
                )
            )
            self._services.value = (
                "PostreSQL: {} - MongoDB: {} - Memcache: {} - Sentry: {} - FTP: {} - Ngrok: {}".format(
                    self.check_server("postgres", "server"),
                    self.check_server("mongodb", "server"),
                    self.check_server("memcache", "server"),
                    self.check_server("sentry", "server"),
                    self.check_server("geru-ftp", "server"),
                    self.check_server("geru-ngrok", "server")
                )
            )

        # Now redraw as normal
        super(StatusFrame, self)._update(frame_no)

    @property
    def frame_update_count(self):
        """Summary

        Returns:
            TYPE: Description
        """
        # Refresh once every 2 seconds by default.
        return 40


def status(screen):
    """Summary

    Args:
        screen (TYPE): Description
    """
    screen.play([Scene([StatusFrame(screen)], -1)], stop_on_resize=True)


def main():
    """Summary
    """
    while True:
        try:
            Screen.wrapper(status, catch_interrupt=True)
            sys.exit(0)
        except ResizeScreenError:
            pass


arguments = docopt(__doc__, version="1.0")
DOCKER_COMPOSE_DIR = arguments['<path>']
DOCKER_COMPOSE_PATH = os.path.join(DOCKER_COMPOSE_DIR, "docker-compose.yml")

try:
    with open(DOCKER_COMPOSE_PATH, 'r') as file:
        COMPOSE_DATA = yaml.load(file.read())
except IOError as exc:
    console.error("Cannot open file: {}".format(exc))
    sys.exit(1)
except yaml.YAMLError as exc:
    console.error("Cannot read file: {}".format(exc))
    sys.exit(1)


if __name__ == "__main__":
    main()
