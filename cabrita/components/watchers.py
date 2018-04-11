# def get_check_status(self):
#     """Check Docker-Compose and Ngrok status.
#
#     Returns
#     -------
#         obj: gui.Text
#
#     """
#     # Check docker-compose.yml status
#     ret = run_command(
#         "cd {} && git fetch && git status -bs --porcelain".format(
#             self.path),
#         get_stdout=True
#     )
#     if not ret:
#         text = formatStr.warning(
#             "Can't find Docker-Compose status.\n",
#             use_prefix=False)
#     elif 'behind' in ret:
#         text = formatStr.error(
#             'Docker-Compose is OUTDATED.\n',
#             use_prefix=False)
#     else:
#         text = formatStr.success(
#             'Docker-Compose is up-to-date.\n',
#             use_prefix=False)
#     # Check Ngrok
#     if self.check_ngrok:
#         try:
#             ret = requests.get(
#                 "http://127.0.0.1:4040/api/tunnels", timeout=1)
#             if ret.status_code == 200:
#                 text += formatStr.success("Ngrok status: running",
#                                           use_prefix=False)
#             else:
#                 text += formatStr.error("Ngrok status: ERROR",
#                                         use_prefix=False)
#         except KeyboardInterrupt:
#             raise KeyboardInterrupt
#         except BaseException:
#             text += formatStr.error("Ngrok status: NOT RUNNING",
#                                     use_prefix=False)
#     return gui.Text(text, border_color=5, title="Check Status")
import os
import re
from typing import List

import psutil
from buzio import formatStr
from dashing import dashing
from tabulate import tabulate

from cabrita.abc.utils import run_command
from cabrita.components.box import Box


class DockerComposeWatch(Box):

    def __init__(self, **kwargs):
        self.config = kwargs.pop('config')
        super(DockerComposeWatch, self).__init__(**kwargs)

    def run(self):
        table_lines = []
        for file in self.config.compose_files:
            full_path = self.config.get_compose_path(file)
            path = os.path.dirname(full_path)
            filename = os.path.splitext(os.path.basename(full_path))[0]
            git_revision = self.git.get_git_revision_from_path(path)
            git_state = self.git.get_behind_state(path)

            table_data = [filename, git_state, git_revision]
            table_lines.append(table_data)

        table_lines = self.format_revision(table_lines)

        table = tabulate(table_lines, [])

        self._widget = dashing.Text(table, color=6, border_color=5, background_color=self.background_color, title="Docker-Compose")


class UserWatch(Box):

    _watchers: List[str] = []

    def run(self):
        self._widget = dashing.Text("Hello World", color=6, border_color=5, background_color=self.background_color, title="Watchers")

    def add_watch(self, watch: str) -> None:
        self._watchers.append(watch)


class SystemWatch(Box):

    def __init__(self, **kwargs):
        self.version = kwargs.pop('version')
        super(SystemWatch, self).__init__(**kwargs)

    def _get_docker_folder_size(self):
        multiple = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024
        }
        total_size: float = 0
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
            title=f"Cabrita v. {self.version}"
        )
