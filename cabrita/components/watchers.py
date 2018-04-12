import os
import re
from datetime import datetime, timedelta
from typing import List

import psutil
from buzio import formatStr
from dashing import dashing
from tabulate import tabulate

from cabrita.abc.utils import run_command
from cabrita.components.box import Box


class Watch(Box):

    @property
    def interval(self):
        return self._interval if self._interval else 0.50

    @interval.setter
    def interval(self, value):
        self._interval = value


class DockerComposeWatch(Watch):

    def __init__(self, **kwargs):
        self.config = kwargs.pop('config')
        super(DockerComposeWatch, self).__init__(**kwargs)
        self.interval = 15
        self.last_update = datetime.now() - timedelta(seconds=self.interval)

    def run(self):
        if not self.can_update:
            return
        table_lines = []
        for file in self.config.compose_files:
            full_path = self.config.get_compose_path(file, os.path.dirname(file))
            path = os.path.dirname(full_path)
            filename = os.path.splitext(os.path.basename(full_path))[0]
            git_revision = self.git.get_git_revision_from_path(path)
            git_state = self.git.get_behind_state(path)

            table_data = [filename, git_state, git_revision]
            table_lines.append(table_data)

        table_lines = self.format_revision(table_lines)

        table = tabulate(table_lines, [])

        self._widget = dashing.Text(table, color=6, border_color=5, background_color=self.background_color,
                                    title="Docker-Compose")


class UserWatch(Watch):

    def __init__(self, **kwargs):
        super(UserWatch, self).__init__(**kwargs)
        self._watchers = []

    def run(self):
        self._widget = dashing.Text("Hello World", color=6, border_color=5, background_color=self.background_color,
                                    title="Watchers")

    def add_watch(self, watch: str) -> None:
        self._watchers.append(watch)


class SystemWatch(Watch):

    def __init__(self, **kwargs):
        self.version = kwargs.pop('version')
        super(SystemWatch, self).__init__(**kwargs)

    @staticmethod
    def _get_docker_folder_size():
        multiple = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024
        }
        total_size = 0.0
        docker_sizes = run_command(
            "docker system df --format '{{.Size}}'",
            get_stdout=True
        )
        for line in docker_sizes.split("\n"):
            if not line:
                continue
            value = re.sub(r'[A-Za-z]+', '', line)
            size = re.sub(r'[0-9\.]+', '', line)
            m = [
                multiple[key]
                for key in multiple
                if key == size
            ][0]
            total_size += float(value) * m

        return total_size

    def run(self):
        """Get machine info using PSUtil.

        Returns
        -------
            obj: dashing.HSplit instance

        """
        cpu_percent = round(psutil.cpu_percent(interval=None) * 10, 0) / 10
        free_memory = int(psutil.virtual_memory().available / 1024 / 1024)
        total_memory = int(psutil.virtual_memory().total / 1024 / 1024)
        memory_percent = (free_memory / total_memory) * 100
        free_space = round(psutil.disk_usage("/").free / 1024 / 1024 / 1024, 1)
        total_space = round(psutil.disk_usage(
            "/").total / 1024 / 1024 / 1024, 1)
        space_percent = (free_space / total_space) * 100
        docker_usage = round(self._get_docker_folder_size() / 1024 / 1024 / 1024, 1)
        docker_percentage = (docker_usage / (total_space - free_space)) * 100

        if memory_percent > 100:
            memory_percent = 100

        if space_percent > 100:
            space_percent = 100

        if docker_percentage > 100:
            docker_percentage = 100

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

        if docker_percentage <= 33:
            docker_color = 2
        else:
            docker_color = 3

        self._widget = dashing.VSplit(
            dashing.HSplit(
                dashing.HGauge(
                    val=cpu_percent,
                    color=cpu_color,
                    border_color=cpu_color,
                    title="CPU:{}%".format(cpu_percent),
                    background_color=self.background_color
                ),
                dashing.HGauge(
                    val=memory_percent,
                    color=memory_color,
                    border_color=memory_color,
                    title="Free Mem:{}M".format(free_memory),
                    background_color=self.background_color
                ),
                dashing.HGauge(
                    val=space_percent,
                    color=space_color,
                    border_color=space_color,
                    title="Free Space:{}Gb".format(free_space),
                    background_color=self.background_color
                )
            ),
            dashing.HGauge(
                val=docker_percentage,
                color=docker_color,
                border_color=docker_color,
                title="Docker Space Used:{}Gb of {}Gb used".format(docker_usage, round(total_space - free_space, 1)),
                background_color=self.background_color
            ),
            title="Cabrita v. {}".format(self.version)
        )
