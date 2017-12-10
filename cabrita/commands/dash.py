
import os
import psutil
import re
import sys
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

    def get_compose_data(self):
        if self.path:
            self.data = get_yaml(self.path, 'docker-compose.yml')
        else:
            self.data = get_yaml(
                path=self.config['docker-compose']['path'],
                file=self.config['docker-compose']['name']
            )
        self.services = sorted(self.data['services'])

    def get_services(self):
        categories = self.config['categories']
        infra_list = self.config['infra']
        ignore = self.config['ignore']
        table_header = ["Name", "Branch", "Git", "Service"] + categories
        table_lines = []
        for key in self.services:
            jump = False
            for i in ignore:
                if i.lower() in key.lower():
                    jump = True
            if jump:
                continue
            for name in categories:
                if name.lower() in key.lower():
                    jump = True
            if jump:
                continue
            for infra in infra_list:
                if infra.lower() in key.lower():
                    jump = True
            if jump:
                continue
            table_data = [
                key,
                self._get_branch(key),
                self._get_git_status(),
                self._check_server(key),
            ]
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
        return dashing.Text(text, color=6, border_color=5, title="Docker Apps")

    def get_infra(self):
        table_header = ["Name", "Status"]
        table_lines = []
        for infra in sorted(self.config['infra']):
            for service in sorted(self.data['services']):
                if service in self.config['ignore']:
                    continue
                if infra.lower() in service.lower():
                    table_data = [
                        service,
                        self._check_server(service)
                    ]
                    table_lines.append(table_data)

        text = tabulate(
            table_lines,
            table_header
        )
        return dashing.Text(text, color=6, border_color=5, title="Docker Infra")

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
            cpu_border_color = 2
        elif cpu_percent <= 70:
            cpu_border_color = 3
        else:
            cpu_border_color = 1

        if memory_percent <= 20:
            memory_border_color = 1
        elif memory_percent <= 50:
            memory_border_color = 3
        else:
            memory_border_color = 2

        if space_percent <= 20:
            space_border_color = 1
        elif space_percent <= 50:
            space_border_color = 3
        else:
            space_border_color = 2

        widget = dashing.HSplit(
            dashing.ColorRangeVGauge(
                val=cpu_percent,
                colormap=((50, 2), (70, 3), (100, 1)),
                border_color=cpu_border_color,
                title="CPU:{}%".format(cpu_percent)
            ),
            dashing.ColorRangeVGauge(
                val=memory_percent,
                colormap=((20, 1), (50, 3), (100, 2)),
                border_color=memory_border_color,
                title="Free Mem:{}M".format(free_memory)
            ),
            dashing.ColorRangeVGauge(
                val=space_percent,
                colormap=((20, 1), (50, 3), (100, 2)),
                border_color=space_border_color,
                title="Free Space:{}Gb".format(free_space)
            )
        )
        return widget

    def get_log(self):
        if not self.log:
            # First time
            self.log = dashing.Log(
                date_format=self.config['logging']['date_format'],
                title="Log",
                color=6,
                border_color=5
            )
            self.log.info("Cabrita started.Press CTRL-C to end.")
        # Check stack-manager
        ret = run_command(
            "cd {} && git status -bs --porcelain".format(self.path),
            get_stdout=True
        )
        if 'behind' in ret:
            self.log.warn('Docker-Compose file is outdated.')

        self.log.info("Testing width")
        return self.log

    def run(self):
        self.get_compose_data()
        term = Terminal()
        with term.fullscreen():
            with term.hidden_cursor():
                try:
                    while True:
                        services = self.get_services()
                        infra = self.get_infra()
                        log = self.get_log()
                        info = self.get_info()
                        ui = dashing.HSplit(
                            services,
                            dashing.HSplit(
                                infra,
                                log,
                                info
                            ),
                            terminal=term,
                            main=True
                        )
                        ui.display()
                        sleep(2)
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

    def _get_git_status(self):
        """Summary

        Returns:
            TYPE: Description
        """
        text = "--"
        if self.repo.is_dirty():
            text = formatStr.info("Modified", use_prefix=False)
        ret = run_command(
            "cd {} && git status -bs --porcelain".format(self.repo.working_dir),
            get_stdout=True
        )
        if "behind" in ret:
            text = formatStr.warning("Need to Pull", use_prefix=False)
        elif "ahead" in ret:
            text = formatStr.warning("Need to Push", use_prefix=False)
        return text

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
                text = formatStr.success("Running", use_prefix=False)
            else:
                text = formatStr.error("Stop", use_prefix=False)
        return text
