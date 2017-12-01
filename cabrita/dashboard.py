"""Cabrita.

Usage:
  cabrita -f <path>
  cabrita -h | --help
  cabrita --version

Options:
  -h --help     Show this screen.
  --version     Show version.
"""
from asciimatics.event import KeyboardEvent
from asciimatics.widgets import Frame, Layout, MultiColumnListBox, Widget, Label, TextBox
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, StopApplication
import yaml
import sys
from collections import defaultdict
import subprocess
from git import Repo
from buzio import formatStr
from docopt import docopt
import re
import os
try:
    import psutil
except ImportError:
    print("This sample requires the psutil package.")
    print("Please run `pip install psutil` and try again.")
    sys.exit(0)


def run_command(
        task,
        get_stdout=False,
        run_stdout=False):
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


class DemoFrame(Frame):
    def __init__(self, screen):
        super(DemoFrame, self).__init__(screen,
                                        screen.height,
                                        screen.width,
                                        has_border=False,
                                        name="My Form")
        # Internal state required for doing periodic updates
        self._last_frame = 0
        self._sort = 5
        self._reverse = True
        self.dc_path = dc_path

        # Create the basic form layout...
        layout = Layout([1], fill_frame=True)
        self._header = TextBox(1, as_string=True)
        self._header.disabled = True
        self._header.custom_colour = "label"
        self._services = TextBox(1, as_string=True)
        self._services.custom_colour = "label"
        self._list = MultiColumnListBox(
            Widget.FILL_FRAME,
            [16, 25, 20, 10, 10, 10, 10, "100%"],
            [],
            titles=["Project", "Branch", "Git", "Server", "Worker", "Beat", "Flower", "Redis"],
            name="mc_list")
        self.add_layout(layout)
        layout.add_widget(self._header)
        layout.add_widget(self._services)
        layout.add_widget(self._list)
        layout.add_widget(
            Label("File: {}. Press `q` to quit.".format(self.dc_path)))
        self.fix()

        # Add my own colour palette
        self.palette = defaultdict(
            lambda: (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK))
        for key in ["selected_focus_field", "label"]:
            self.palette[key] = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK)
        self.palette["title"] = (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE)

    def process_event(self, event):
        # Do the key handling for this Frame.
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord('q'), ord('Q'), Screen.ctrl("c")]:
                raise StopApplication("User quit")

            # Force a refresh for improved responsiveness
            self._last_frame = 0

        # Now pass on to lower levels for normal handling of the event.
        return super(DemoFrame, self).process_event(event)

    def get_branch(self, name):
        if compose_data['services'][name].get('build'):
            data = compose_data['services'][name]['build']['context']
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
        if service_type != "server":
            full_name = "{}-{}".format(name, service_type)
        else:
            full_name = name
        found = [
            k
            for k in compose_data['services']
            if k == full_name
        ]
        if not found:
            text = "--"
        else:
            ret = run_command(
                'docker ps | grep "{0}$\|{0}_run"'.format(full_name),
                get_stdout=True
            )
            if ret:
                text = "Running"
            else:
                text = "Stop"
        return text

    def _update(self, frame_no):
        # Refresh the list view if needed
        if frame_no - self._last_frame >= self.frame_update_count or self._last_frame == 0:
            self._last_frame = frame_no

            # Create the data to go in the multi-column list...
            last_selection = self._list.value
            last_start = self._list.start_line
            list_data = []
            for key in compose_data['services']:
                self.service = compose_data['services'][key]
                service_type = "".join(key.split("-")[-1])
                if service_type.lower() in ['worker', 'beat', 'flower', 'redis'] \
                        and key != "banks-worker":
                    continue
                if key in ['postgres', 'mongodb', 'migrate', 'memcache', 'traefik']:
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
                    "PostreSQL: {}    MongoDB: {}    Memcache: {}    Sentry: {}".format(
                        self.check_server("postgres", "server"),
                        self.check_server("mongodb", "server"),
                        self.check_server("memcache", "server"),
                        self.check_server("sentry", "server"),
                    )
                )

        # Now redraw as normal
        super(DemoFrame, self)._update(frame_no)

    @property
    def frame_update_count(self):
        # Refresh once every 2 seconds by default.
        return 40


def demo(screen):
    screen.play([Scene([DemoFrame(screen)], -1)], stop_on_resize=True)


arguments = docopt(__doc__, version="1.0")
dc_path = arguments['<path>']

if os.path.isfile(dc_path):
    with open(dc_path, 'r') as file:
        compose_data = yaml.load(file.read())
else:
    raise ValueError("File invalid")


def main():
    while True:
        try:
            Screen.wrapper(demo, catch_interrupt=True)
            sys.exit(0)
        except ResizeScreenError:
            pass


if __name__ == "__main__":
    main()
