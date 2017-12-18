
import os
import psutil
import re
import sys
import requests
import json
from blessed import Terminal
from buzio import formatStr
from cabrita import dashing
from git import Repo
from tabulate import tabulate
from time import sleep
from cabrita.utils import run_command, get_yaml


class Dashboard():

    def __init__(self, docker_compose_path, config):
        self.path = docker_compose_path
        self.data = None
        self.services = None
        self.config = config
        self.log = None
        self.included_services = []

    def get_compose_data(self):
        if self.path:
            if "$" in self.path:
                converted_path_list = []
                path_list = os.path.split(self.path)
                for p in path_list:
                    if "$" in p:
                        s = re.search(r"\$(\w+)", p)
                        if s:
                            env = os.environ.get(s.group(1))
                        else:
                            env = p
                    converted_path_list.append(env)
                self.path = os.path.join(**converted_path_list)
            self.data = get_yaml(self.path, 'docker-compose.yml')
        else:
            self.path = self.config['docker-compose']['path']
            if "$" in self.path:
                converted_path_list = []
                path_list = os.path.split(self.path)
                for p in path_list:
                    env = p
                    if "$" in p:
                        s = re.search(r"\$(\w+)", p)
                        if s:
                            env = os.environ.get(s.group(1))
                    converted_path_list.append(env)
                self.path = os.path.join(*converted_path_list)
            self.data = get_yaml(
                path=self.path,
                file=self.config['docker-compose']['name']
            )
        self.services = sorted(self.data['services'])

    def get_data_from_version(self):
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
        elif version == 1:
            self.boxes = self.config['box']
            self.interval = self.config.get('interval', 2)
            self.layout = self.config.get('layout', 'horizontal')
            self.check_ngrok = self.config.get('check', {}).get('ngrok', False)
            self.ignore = self.config.get('ignore', [])

    def _make_box(self, box):
        table_lines = []
        table_header = ['Service']
        show_git = box.get('show_git', True)
        categories = box.get('categories', [])
        list_only = box.get('list_only', [])
        box_name = box.get('name', box)
        for key in self.services:
            if key in self.included_services:
                continue
            jump = False
            for i in self.ignore:
                if i.lower() in key.lower():
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
            table_header = ["Service"]
            if show_git:
                table_header += ["Git"]
            table_header += categories
            table_data = [
                self.get_status(key=key)
            ]
            if show_git:
                table_data.append(self._get_git_status(key))
            self.included_services.append(key)
            for cat in categories:
                for search in self.services:
                    if key.lower() in search.lower() and cat.lower() in search.lower():
                        table_data.append(self._check_server(search))
                        continue

            table_lines.append(table_data)

        text = tabulate(
            table_lines,
            table_header
        )
        return dashing.Text(text, color=6, border_color=5, title=box_name)

    def get_status(self, key):
        docker_info = json.loads(
            run_command(
                task="docker inspect {}".format(key),
                get_stdout=True
            )
        )[0]
        if docker_info['State']['Running']:
            theme = "success"
        elif docker_info['State']['Paused']:
            theme = "warning"
        elif docker_info['State']['Restarting']:
            theme = "info"
        else:
            theme = "error"
        return formatStr.info(key, theme=theme, use_prefix=False)

    def get_layout(self, term):
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
        st = dashing.VSplit(
            log,
            dashing.VSplit(
                check_status,
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

    def get_info(self):
        cpu_percent = round(psutil.cpu_percent(interval=None) * 10, 0) / 10
        free_memory = int(psutil.virtual_memory().available / 1024 / 1024)
        total_memory = int(psutil.virtual_memory().total / 1024 / 1024)
        memory_percent = (free_memory / total_memory) * 100
        free_space = round(psutil.disk_usage("/").free / 1024 / 1024 / 1024, 1)
        space_percent = round(psutil.disk_usage("/").percent * 10, 0) / 10

        if memory_percent > 100:
            memory_percent = 100

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

        widget = dashing.HSplit(
            dashing.HGauge(
                val=cpu_percent,
                color=cpu_color,
                border_color=cpu_color,
                title="CPU:{}%".format(cpu_percent)
            ),
            dashing.HGauge(
                val=memory_percent,
                color=memory_color,
                border_color=memory_color,
                title="Free Mem:{}M".format(free_memory)
            ),
            dashing.HGauge(
                val=space_percent,
                color=space_color,
                border_color=space_color,
                title="Free Space:{}Gb".format(free_space)
            )
        )
        return widget

    def get_log(self):
        if not self.log:
            # First time checks
            self.log = dashing.Log(
                date_format=self.config['logging']['date_format'],
                title="Log",
                color=6,
                border_color=5
            )
            self.log.info("Cabrita has started.Press CTRL-C to end.")
        
        # Unwatched services
        if self.included_services:
            name_list = [
                service
                for service in self.services
                if service not in self.included_services and service not in self.ignore
            ]
            for name in name_list:
                self.log.warn("Not watched: {}".format(name))
        return self.log

    def get_check_status(self):
        # Check stack-manager
        ret = run_command(
            "cd {} && git fetch && git status -bs --porcelain".format(self.path),
            get_stdout=True
        )
        if not ret:
            text = formatStr.warning("Can't find Docker-Compose status.\n", use_prefix=False)
        elif 'behind' in ret:
            text = formatStr.error('Docker-Compose file is OUTDATED.\n', use_prefix=False)
        else:
            text = formatStr.success('Docker-Compose file is up-to-date.\n', use_prefix=False)
        # Check Ngrok
        if self.check_ngrok:
            try:
                ret = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=1)
                if ret.status_code == 200:
                    text += formatStr.success("Ngrok is running", use_prefix=False)
                else:
                    text += formatStr.error("Ngrok is returning ERROR", use_prefix=False)
            except BaseException:
                text += formatStr.error("Ngrok is NOT RUNNING", use_prefix=False)
        return dashing.Text(text, border_color=5, title="Check Status")

    def run(self):
        self.get_compose_data()
        self.get_data_from_version()
        term = Terminal()
        with term.fullscreen():
            with term.hidden_cursor():
                try:
                    while True:
                        self.included_services = []
                        ui = self.get_layout(term)
                        ui.display()
                        sleep(self.interval)
                except KeyboardInterrupt:
                    print(term.color(0))
                    sys.exit(0)

    def _get_branch(self, name):
        """Summary

        Args:
            name (TYPE): Description

        Returns:
            TYPE: Description
        """
        if self.data['services'][name].get('build'):
            data = self.data['services'][name]['build']['context']
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

    def _get_git_status(self, key):
        """Summary

        Returns:
            TYPE: Description
        """
        if not self.data['services'][key].get('build', False):
            return ""
        up = u'▲'
        down = u'▼'
        text = "{} ".format(self._get_branch(key))
        theme = "success"
        if self.repo.is_dirty():
            theme = "warning"
        ret = run_command(
            "cd {} && git status -bs --porcelain".format(self.repo.working_dir),
            get_stdout=True
        )
        if "ahead" in ret:
            s = re.search(r"ahead (\d+)", ret)
            text += formatStr.success(
                "{} {}".format(up, s.group(1)),
                use_prefix=False
            )
            theme = "info"
        elif "behind" in ret:
            s = re.search(r"behind (\d+)", ret)
            text += formatStr.error(
                "{} {} ".format(down, s.group(1)),
                use_prefix=False
            )
            theme = "warning"
        return formatStr.success(text, theme=theme, use_prefix=False)

    def _check_server(self, name):
        """Summary

        Args:
            name (TYPE): Description
            service_type (TYPE): Description

        Returns:
            TYPE: Description
        """
        found = [
            k
            for k in self.data['services']
            if k == name
        ]
        if not found:
            text = ""
        else:
            ret = run_command(
                'docker ps | grep "{0}$\|{0}_run"'.format(name),
                get_stdout=True
            )
            if ret:
                s = re.search(r"\((\w+)\)", ret)
                if s:
                    text = formatStr.warning(s.group(1), use_prefix=False)
                else:
                    text = formatStr.success("Running", use_prefix=False)
            else:
                text = formatStr.error("Stop", use_prefix=False)
        return text
