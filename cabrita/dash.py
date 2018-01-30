"""Cabrita Dashboard module."""
import os
import psutil
import re
import sys
import requests
import json
import datetime
import threading
from collections import Counter
from raven import Client
from blessed import Terminal
from buzio import formatStr, console
from cabrita import gui
from tabulate import tabulate
from time import sleep
from cabrita.utils import run_command, get_yaml, get_path

UP = u'▲'
DOWN = u'▼'

ARROW_UP = u"↑"
ARROW_DOWN = u"↓"

client = None
if os.getenv('CABRITA_SENTRY_DSN'):
    client = Client(os.getenv('CABRITA_SENTRY_DSN'))


class Dashboard():
    """Dashboard class."""

    def __init__(self, config):
        """Class initialization.

        Args:
            config (dict): config data from yaml file.
        """
        self.data = None
        self.services = None
        self.config = config
        self.log = None
        self.included_services = []
        self.last_git_check = None
        self.can_check_git = False
        self.cache_git = {}
        self.repo = None

    def get_compose_data(self):
        """Get data from docker-compose.yml.

        Convert services key in docker-compose.yml
        to python dict stored in self.services
        """
        self.path = self.config['docker-compose']['path']
        if "$" in self.path:
            converted_path_list = []
            path_list = os.path.split(self.path)
            for p in path_list:
                env = p
                if "$" in p:
                    s = re.search(r"\$(\w+)", p)
                    if s:
                        env = os.environ.get(s.group(1), None)
                        if not env:
                            console.error(
                                "Can't resolve {}".format(
                                    s.group(1)))
                            sys.exit(1)
                converted_path_list.append(env)
            self.path = os.path.join(*converted_path_list)
        self.data = get_yaml(
            path=self.path,
            file=self.config['docker-compose']['name']
        )
        self.services = sorted(self.data['services'])

    def get_data_from_version(self):
        """Set instance properties.

        Instance properties are set based on
        configuration version indicated in yaml file:

        Version 0: testing version (deprecated)
        Version 1: current version
        """
        version = self.config.get('version', 0)
        if version == 0:
            self.categories = self.config.get('categories', [])
            self.small_list = self.config.get('infra', [])
            self.interval = 2
            self.big_name = "Docker Services"
            self.small_name = "Services"
            self.layout = "horizontal"
            self.check_ngrok = True
            self.ignore = self.config.get('ignore', [])
            self.fetch = 30
        elif version == 1:
            self.boxes = self.config['box']
            self.interval = self.config.get('interval', 2)
            self.layout = self.config.get('layout', 'horizontal')
            self.check_ngrok = self.config.get('check', {}).get('ngrok', False)
            self.ignore = self.config.get('ignore', [])
            self.fetch = self.config.get('fetch_each', 30)

    def _make_box(self, box):
        """Generate box data.

        Iterate all services from docker-compose.yml, ignoring:
            1. Already processed services (in previous processed boxes)
            2. Ignored services (from 'ignore' list parameter)
            2. Recognized as category (from 'categories' list parameter)

        Check if service must be inside this box, using:
            1. 'filter' list parameter
            2. 'list_only' list parameter
            3. 'catch_all' parameter (if this is the last box)

        If service must be inside this box:
            1. get formatted service name (by status)
            2. get formatted service status (by status)
            3. Show git branch info (from 'show_git' parameter)
            4. Iterate all possible category services
               derived from this service

        Args:
            box (dict): box to process

        Returns
        -------
            obj: gui.Text instance

        """
        table_lines = []
        table_header = ['Service']
        show_git = box.get('show_git', True)
        categories = box.get('categories', [])
        list_only = box.get('list_only', [])
        box_name = box.get('name', box)
        box_filter = box.get('filter', "")
        for key in self.services:
            if key in self.included_services:
                continue
            jump = False
            for i in self.ignore:
                if i.lower() in key.lower():
                    jump = True
            if box_filter and box_filter.lower() not in key.lower():
                jump = True
            if jump:
                continue
            for name in categories:
                if name.lower() in key.lower():
                    jump = True
            if jump:
                continue
            if list_only:
                jump = True
                for s in list_only:
                    if s.lower() in key.lower():
                        jump = False
                if jump:
                    continue
            table_header = ["Service", "Status"]
            if show_git:
                table_header += ["Git"]
            table_header += categories
            table_data = [
                self.get_service_name(key),
                self._check_server(name=key)
            ]
            if show_git:
                table_data.append(self._get_git_status(key, box))
            self.included_services.append(key)
            for cat in categories:
                found = False
                for search in self.services:
                    if "_" in key:
                        k = key.lower().split("_")[0]
                    elif "-" in key:
                        k = key.lower().split("-")[0]
                    else:
                        k = key.lower()
                    if k in search.lower() and cat.lower() in search.lower():
                        table_data.append(self._check_server(search))
                        self.included_services.append(search)
                        found = True
                        continue
                if not found:
                    table_data.append(
                        formatStr.info("--", theme="dark", use_prefix=False)
                    )

            table_lines.append(table_data)

        text = tabulate(
            table_lines,
            table_header
        )
        return gui.Text(text, color=6, border_color=5, title=box_name)

    def get_service_name(self, key):
        """Return service name.

        Return formatted service name,
        based on docker inspect information.

        Args:
            key (string): Service name

        Returns
        -------
            string: formatted string for key

        """
        try:
            ret = self._inspect_service(key)
            if not ret:
                return formatStr.info(key, theme="dark", use_prefix=False)
            elif "not found" in ret.lower() or "exited" in ret.lower():
                return formatStr.info(key, theme="dark", use_prefix=False)
            else:
                return formatStr.info(key, use_prefix=False)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except BaseException as exc:
            return formatStr.info(key, theme="error", use_prefix=False)

    def get_layout(self, term):
        """Generate the dashboard layout.

        First, get the logs, machine info and docker-compose/ngrok status
        Then generate layout for each box configured in yaml file.

        Args:
            term (obj): Python Terminal instance

        Returns
        -------
            obj: HSplit or VSplit instance

        """
        log = self.get_log()
        info = self.get_info()
        check_status = self.get_check_status()
        large_boxes = []
        small_boxes = []
        last_box = None
        for box in self.boxes:
            current_box = self.boxes[box]
            if current_box.get('catch_all', False):
                last_box = current_box
                continue
            size = current_box.get('size', 'small')
            if size == "small":
                small_boxes.append(self._make_box(current_box))
            else:
                large_boxes.append(self._make_box(current_box))
        size = last_box.get('size', 'small')
        if size == "small":
            small_boxes.insert(0, self._make_box(last_box))
        else:
            large_boxes.insert(0, self._make_box(last_box))

        sm = None
        lg = None
        if large_boxes:
            lg = large_boxes
        st = gui.VSplit(
            log,
            gui.VSplit(
                check_status,
                info
            )
        )
        if small_boxes:
            sm = gui.HSplit(*small_boxes, st)
        else:
            sm = st
        if self.layout == "horizontal":
            func = gui.HSplit
        else:
            func = gui.VSplit
        if not lg:
            ui = func(sm, terminal=term, main=True)
        else:
            ui = func(*lg, sm, terminal=term, main=True)

        return ui

    def get_info(self):
        """Get machine info using PSUtil.

        Returns
        -------
            obj: gui.HSplit instance

        """
        cpu_percent = round(psutil.cpu_percent(interval=None) * 10, 0) / 10
        free_memory = int(psutil.virtual_memory().available / 1024 / 1024)
        total_memory = int(psutil.virtual_memory().total / 1024 / 1024)
        memory_percent = (free_memory / total_memory) * 100
        free_space = round(psutil.disk_usage("/").free / 1024 / 1024 / 1024, 1)
        total_space = round(psutil.disk_usage(
            "/").total / 1024 / 1024 / 1024, 1)
        space_percent = (free_space / total_space) * 100

        if memory_percent > 100:
            memory_percent = 100

        if space_percent > 100:
            space_percent = 100

        if cpu_percent <= 50:
            cpu_color = 2
        elif cpu_percent <= 70:
            cpu_color = 3
        else:
            cpu_color = 1

        if memory_percent <= 20:
            memory_color = 1
        elif memory_percent <= 50:
            memory_color = 3
        else:
            memory_color = 2

        if space_percent <= 20:
            space_color = 1
        elif space_percent <= 50:
            space_color = 3
        else:
            space_color = 2

        widget = gui.HSplit(
            gui.HGauge(
                val=cpu_percent,
                color=cpu_color,
                border_color=cpu_color,
                title="CPU:{}%".format(cpu_percent)
            ),
            gui.HGauge(
                val=memory_percent,
                color=memory_color,
                border_color=memory_color,
                title="Free Mem:{}M".format(free_memory)
            ),
            gui.HGauge(
                val=space_percent,
                color=space_color,
                border_color=space_color,
                title="Free Space:{}Gb".format(free_space)
            )
        )
        return widget

    def get_log(self):
        """Generate logs.

        Returns
        -------
            obj: gui.Log instance

        """
        if not self.log:
            # First time checks
            self.log = gui.Log(
                date_format=self.config['logging']['date_format'],
                title="Log",
                color=6,
                border_color=5
            )
            self.log.info("Cabrita has started.")
            self.log.info("Press CTRL-C to end.")

        # Unwatched services
        if self.included_services:
            name_list = [
                service
                for service in self.services
                if service not in self.included_services and
                service not in self.ignore
            ]
            for name in name_list:
                self.log.warn("Not watched: {}".format(name))
        return self.log

    def get_check_status(self):
        """Check Docker-Compose and Ngrok status.

        Returns
        -------
            obj: gui.Text

        """
        # Check docker-compose.yml status
        ret = run_command(
            "cd {} && git fetch && git status -bs --porcelain".format(
                self.path),
            get_stdout=True
        )
        if not ret:
            text = formatStr.warning(
                "Can't find Docker-Compose status.\n",
                use_prefix=False)
        elif 'behind' in ret:
            text = formatStr.error(
                'Docker-Compose is OUTDATED.\n',
                use_prefix=False)
        else:
            text = formatStr.success(
                'Docker-Compose is up-to-date.\n',
                use_prefix=False)
        # Check Ngrok
        if self.check_ngrok:
            try:
                ret = requests.get(
                    "http://127.0.0.1:4040/api/tunnels", timeout=1)
                if ret.status_code == 200:
                    text += formatStr.success("Ngrok status: running",
                                              use_prefix=False)
                else:
                    text += formatStr.error("Ngrok status: ERROR",
                                            use_prefix=False)
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except BaseException:
                text += formatStr.error("Ngrok status: NOT RUNNING",
                                        use_prefix=False)
        return gui.Text(text, border_color=5, title="Check Status")

    def run(self):
        """Run main class code.

        Get data from docker-compose, set instance properties using
        yaml configuration file and start a infinite loop for the dashboard.

        Stops at Error or typing CTRL-C.
        """
        try:
            self.get_compose_data()
            self.get_data_from_version()
            term = Terminal()

            with term.fullscreen():
                with term.hidden_cursor():
                    while True:
                        self.check_time()
                        self.included_services = []
                        ui = self.get_layout(term)
                        ui.display()
                        sleep(self.interval)
        except KeyboardInterrupt:
            print(term.color(0))
            sys.exit(0)
        except BaseException as exc:
            console.error("Internal Error: {}".format(exc))
            if client:
                client.captureException()
            sys.exit(1)

    def _get_branch(self, name, box):
        """Get branch data for service.

        Check if service has build context inside docker-compose
        Try to get git branch information using build context path
        If success and 'target_branch' parameter is set to current box,
        try to get commit diff between current branch and target branch.

        Args:
            name (string): Service name
            box (dict): Box

        Returns
        -------
            String: branch information

        """
        if self.data['services'][name].get('build'):
            data = self.data['services'][name]['build']
            if isinstance(data, str):
                raw_path = data
            else:
                raw_path = self.data['services'][name]['build']['context']

            path = get_path(raw_path, self.path)

            repo = run_command(
                "cd {} && git branch | grep \"*\" 2>/dev/null".format(path),
                get_stdout=True
            )
            if repo:
                dirty = run_command(
                    "cd {} && git status --porcelain 2>/dev/null".format(path),
                    get_stdout=True
                )
                self.repo = {
                    'name': repo.replace("* ", "").replace("\n", ""),
                    'path': path,
                    'dirty': True if dirty else False
                }
                text = self.repo['name']
                target_branch = box.get("target_branch", False)
                if target_branch and \
                    self.repo['name'] != target_branch.replace(
                        "origin/", ""):
                    lines_behind = 0
                    behind = run_command(
                        "cd {} && git log {}..{} --oneline 2>/dev/null".format(
                            path, text, target_branch),
                        get_stdout=True
                    )
                    if behind:
                        lines_behind = len(behind.split("\n"))
                    if lines_behind:
                        text += " ({}: ".format(target_branch)
                        if lines_behind > 0:
                            text += formatStr.error(
                                "{} {}".format(
                                    ARROW_DOWN, lines_behind - 1),
                                use_prefix=False
                            )
                        text += ")"
            else:
                text = formatStr.warning(
                    "Branch Not Found", use_prefix=False)
        else:
            text = formatStr.info("Using Image", use_prefix=False)
        return text

    def run_fetch(self):
        """Thread routine for git fetch.

        Run 'git fetch' command.
        Must be called inside a Python Thread instance.

        """
        try:
            run_command(
                "cd {} && git fetch --all -q 2>/dev/null".format(
                    self.repo['path']),
                get_stdout=True
            )
        except KeyboardInterrupt:
            raise KeyboardInterrupt

    def check_time(self):
        """Check time for git refresh data."""
        self.can_check_git = False
        if not self.last_git_check:
            self.last_git_check = datetime.datetime.now()
            self.can_check_git = True
        else:
            now = datetime.datetime.now()
            time_elapsed = now - self.last_git_check
            if time_elapsed.seconds >= self.fetch:
                self.last_git_check = now
                self.can_check_git = True

    def _get_git_status(self, key, box):
        """Retrieve Git Status from cache or command.

        Checks every 'fetch_each' seconds.
        Starts a thread for the 'git fetch --all' command

        Args:
            key (string): Service name
            box (dict): Current box
        """
        if not self.can_check_git:
            return self.cache_git.get(key, "")

        if not self.data['services'][key].get('build', False):
            return ""
        self.repo = None
        text = "{} ".format(self._get_branch(key, box))
        theme = "dark"
        if self.repo:
            theme = "success"
            if self.repo['dirty']:
                theme = "warning"
            t = threading.Thread(target=self.run_fetch)
            t.start()
            ret = run_command(
                "cd {} && git status -bs --porcelain".format(
                    self.repo['path']),
                get_stdout=True
            )
            if "behind" in ret:
                s = re.search(r"behind (\d+)", ret)
                text += formatStr.error(
                    "{} {} ".format(ARROW_DOWN, s.group(1)),
                    use_prefix=False
                )
            if "ahead" in ret:
                s = re.search(r"ahead (\d+)", ret)
                text += formatStr.error(
                    "{} {} ".format(ARROW_UP, s.group(1)),
                    use_prefix=False
                )
        status = formatStr.success(text, theme=theme, use_prefix=False)
        self.cache_git[key] = status
        return status

    def _check_server(self, name):
        """Get service docker status.

        Run 'docker inspect <name>' and retrieve the response dict
        If not found <name> try to find:

        1. Intermediate containers: <name>_run
        2. Scaling containers: <name>_1

        Args:
            name (string): service name

        Returns
        -------
            str: formatted string with status

        """
        found = [
            k
            for k in self.data['services']
            if k == name
        ]
        if not found:
            return ""

        text = self._inspect_service(name)
        if text:
            return text

        cmd = "docker ps | grep {name}"
        services = run_command(
            cmd.format(name=name),
            get_stdout=True
        )
        if services:
            service_list = [
                re.search("\S+$", line).group()
                for line in services.split("\n")
                if re.search("\S+$", line)
            ]
            status_list = [
                self._inspect_service(s)
                for s in service_list
            ]
            count = dict(Counter(status_list))
            line = ", ".join([
                "{}: {}".format(k, count[k])
                for k in count
            ])
            text = formatStr.info(line, use_prefix=False)
        else:
            dc_data = [
                self.data['services'][key]
                for key in self.data['services']
                if self.data['services'][key].get("container_name", "") == name
            ]
            if dc_data:
                text = formatStr.info(
                    "Not Found", theme="dark", use_prefix=False)
            else:
                text = formatStr.info("Stop", theme="dark", use_prefix=False)
        return text

    def _inspect_service(self, name):
        ret = run_command(
            'docker inspect {} 2>/dev/null'.format(name),
            get_stdout=True
        )
        if ret:
            try:
                ret = json.loads(ret)[0]
                if ret['State'].get('Health', False):
                    if ret['State']['Status'].lower() == 'running':
                        stats = ret['State']['Health']['Status'].title()
                    else:
                        stats = ret['State']['Status'].title()
                    if ret['State']['Running']:
                        if ret['State']['Health']['Status'] == 'healthy':
                            theme = "success"
                        else:
                            if ret['State']['Health']['FailingStreak'] > 3:
                                theme = "error"
                            else:
                                theme = "warning"
                    elif ret['State']['Paused']:
                        theme = "warning"
                    elif not ret['State']['Running']:
                        theme = "dark"
                    else:
                        theme = "error"
                else:
                    stats = ret['State']['Status'].title()
                    if ret['State']['Running']:
                        theme = "success"
                    elif ret['State']['Paused']:
                        theme = "warning"
                    elif not ret['State']['Running']:
                        theme = "dark"
                    else:
                        theme = "error"
                text = formatStr.info(stats, theme=theme, use_prefix=False)
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except BaseException as exc:
                text = formatStr.error("Error", use_prefix=False)
        else:
            text = None
        return text
