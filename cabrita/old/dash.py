"""Cabrita Dashboard module."""
import os
import re
import sys
import json
import datetime
import threading
import time
from tzlocal import get_localzone
from collections import Counter
from raven import Client
from blessed import Terminal
from buzio import formatStr, console
from dashing import dashing
from tabulate import tabulate
from time import sleep
from cabrita.core.utils import run_command, get_yaml, get_path
from cabrita.core.services import get_check_services
from cabrita.core.status import get_check_status
from cabrita.core.info import get_info

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
        self.last_long_ops = None
        self.start_long_ops = False
        self.cache_long_ops = {'git': {}, 'status': None}
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
            self.check_ngrok = False
            self.ignore = self.config.get('ignore', [])
            self.fetch = 30
            self.files_to_check = []
            self.status_file_path = "$HOME/.cabrita"
            self.files_to_build = ['Dockerfile']
            self.services_to_check_with_git = []
        elif version == 1:
            self.boxes = self.config['box']
            self.interval = self.config.get('interval', 2)
            self.layout = self.config.get('layout', 'horizontal')
            self.check_ngrok = self.config.get('check', {}).get('ngrok', False)
            self.ignore = self.config.get('ignore', [])
            self.fetch = self.config.get('fetch_each', 30)
            self.files_to_check = self.config.get('files', [])
            self.status_file_path = self.config.get(
                'status_file_path', "$HOME/.cabrita")
            self.files_to_build = self.config.get(
                'build_check', ['Dockerfile'])
            self.services_to_check_with_git = self.config.get(
                'build_check_using_git', [])

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
            obj: dashing.Text instance

        """
        table_lines = []
        table_header = ['Service']
        show_git = box.get('show_git', True)
        categories = box.get('categories', [])
        list_only = box.get('list_only', [])
        box_name = box.get('name', box)
        box_filter = box.get('filter', "")
        show_ports = box.get('show_ports', False)
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
            if show_ports and show_ports == 'column':
                table_header += ['Port']
            if show_git:
                table_header += ["Git"]
            table_header += categories
            service_status = self._check_server(
                name=key, show_ports=show_ports)
            table_data = [
                self.get_service_name(key),
                service_status
            ]
            if show_ports and show_ports == 'column':
                if 'running' in service_status.lower() or\
                        'healthy' in service_status.lower():
                    table_data.append(self._get_service_port(key))
                else:
                    table_data.append('')
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
                        table_data.append(
                            self._check_server(
                                search, show_ports=show_ports))
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
        return dashing.Text(text, color=6, border_color=5, title=box_name)

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
        if not self.start_long_ops:
            check_status = self.cache_long_ops.get('status')
        else:
            check_status = get_check_status(self)
            self.cache_long_ops['status'] = check_status
        check_services = get_check_services(self)
        info = get_info()
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
        st = dashing.VSplit(
            check_status,
            dashing.VSplit(
                check_services,
                info
            )
        )
        if small_boxes:
            sm = dashing.HSplit(*small_boxes, st)
        else:
            sm = st
        if self.layout == "horizontal":
            func = dashing.HSplit
        else:
            func = dashing.VSplit
        if not lg:
            ui = func(sm, terminal=term, main=True)
        else:
            ui = func(*lg, sm, terminal=term, main=True)

        return ui

    def get_log(self):
        """Generate logs.

        Returns
        -------
            obj: dashing.Log instance

        """
        if not self.log:
            # First time checks
            self.log = dashing.Log(
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
        """Check time for start long operations."""
        self.start_long_ops = False
        if not self.last_long_ops:
            self.last_long_ops = datetime.datetime.now()
            self.start_long_ops = True
        else:
            now = datetime.datetime.now()
            time_elapsed = now - self.last_long_ops
            if time_elapsed.seconds >= self.fetch:
                self.last_long_ops = now
                self.start_long_ops = True

    def _get_service_port(self, key):
        external_ports = []
        ports_list = self.data['services'].get(key, {}).get('ports', [])
        external_ports = [
            port.split(":")[0]
            for port in ports_list
            if ":" in port
        ]
        if not external_ports:
            return ""
        elif len(external_ports) == 1:
            return "".join(external_ports)
        else:
            return ",".join(external_ports)

    def _get_git_status(self, key, box):
        """Retrieve Git Status from cache or command.

        Checks every 'fetch_each' seconds.
        Starts a thread for the 'git fetch --all' command

        Args:
            key (string): Service name
            box (dict): Current box
        """
        if not self.start_long_ops:
            return self.cache_long_ops.get('git', {}).get(key, "")

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
        self.cache_long_ops['git'][key] = status
        return status

    def _check_server(self, name, show_ports):
        """Get service docker status.

        Run 'docker inspect <name>' and retrieve the response dict
        If not found <name> try to find:

        1. Intermediate containers: <name>_run
        2. Scaling containers: <name>_1

        Args:
            name (string): service name
            show_ports (obj): False, 'name' or 'column'

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
            if show_ports and show_ports == 'name' and \
                ('running' in text.lower() or
                    'healthy' in text.lower()):
                port = self._get_service_port(name)
                if port:
                    text += " ({})".format(port)
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
            if show_ports and show_ports == 'name' and \
                ('running' in text.lower() or
                    'healthy' in text.lower()):
                port_list = [
                    self._get_service_port(s)
                    for s in service_list
                    if self._get_service_port(s) != ""
                ]
                if port_list:
                    text = text + " ({})".format("".join(port_list))
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

                # Check for build
                test_date = None
                image_name = ret['Config']['Image']
                image_data = run_command(
                    'docker inspect {} 2>/dev/null'.format(image_name),
                    get_stdout=True
                )
                if image_data:
                    image_data = json.loads(image_data)[0]

                    # Get current UTC offset
                    time_now = datetime.datetime.now()
                    time_now_utc = datetime.datetime.utcnow()
                    time_offset_seconds = (
                        time_now - time_now_utc).total_seconds()
                    utc_offset = time.gmtime(abs(time_offset_seconds))
                    utc_string = "{}{}".format(
                        "-" if time_offset_seconds < 0 else "+",
                        time.strftime("%H%M", utc_offset)
                    )
                    date = image_data.get('Created')[:-4] + " " + utc_string
                    test_date = datetime.datetime.strptime(
                        date, "%Y-%m-%dT%H:%M:%S.%f %z")

                label = ret['Config']['Labels']['com.docker.compose.service']
                full_path = None
                if test_date and self.data['services'][label].get('build'):
                    build_path = self.data['services'][label].get('build')
                    if isinstance(build_path, dict):
                        build_path = build_path.get('context')
                    full_path = get_path(build_path, self.path)
                    list_dates = [
                        datetime.datetime.fromtimestamp(
                            os.path.getmtime(os.path.join(full_path, file)),
                            tz=get_localzone()
                        )
                        for file in self.files_to_build
                        if os.path.isfile(os.path.join(full_path, file))
                    ]
                    if list_dates:
                        if max(list_dates) > test_date:
                            stats = "NEED BUILD"
                            theme = "error"

                # Check for build using commit
                # Ex.: 2018-02-23 18:31:45 -0300
                if name in self.services_to_check_with_git \
                        and stats != "NEED BUILD" and full_path:
                    ret = run_command(
                        'cd {} && git log -1 --pretty=format:"%cd" --date=iso'.format(full_path),
                        get_stdout=True
                    )
                    date_fmt = "%Y-%m-%d %H:%M:%S %z"
                    if ret:
                        commit_date = datetime.datetime.strptime(ret, date_fmt)
                        if commit_date > test_date:
                            stats = "NEED BUILD"
                            theme = "error"

                text = formatStr.info(stats, theme=theme, use_prefix=False)
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except BaseException as exc:
                if client:
                    client.captureException()
                text = formatStr.error("Error", use_prefix=False)
        else:
            text = None
        return text
