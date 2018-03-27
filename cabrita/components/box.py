from datetime import datetime
from threading import Thread
from typing import List

from dashing import dashing
from tabulate import tabulate
from buzio import formatStr


class Box(Thread):


    def __init__(self, services: List[str], docker, git):
        super(Box, self).__init__()
        self._widget = ""
        self.last_update = datetime.now()
        self.interval = 0
        self.data = {}
        self.services = services
        self.docker = docker
        self.git = git

    @property
    def can_update(self) -> bool:
        seconds_elapsed = (datetime.now() - self.last_update).total_seconds()
        return seconds_elapsed >= self.interval

    @property
    def widget(self):
        if self.can_update:
            self.run()
        return self._widget


    @widget.setter
    def widget(self, value):
        self._widget = value


    @property
    def show_git(self) -> bool:
        return self.data.get('show_git', True)

    @property
    def show_port(self) -> str:
        return self.data.get('show_port', '')

    @property
    def categories(self) -> List[str]:
        return self.data.get('categories', [])

    @property
    def title(self) -> str:
        return self.data.get('title', 'Box')

    def load_data(self, data: dict):
        self.data = data

    def run(self):
        # Define Headers
        table_header = ['Service', 'Status']
        if self.show_git:
            table_header += ['Git']
        if self.show_port == 'column':
            table_header += ['Port']
        if self.categories:
            table_header += self.categories

        # Generating lines
        table_lines = []
        for service in self.services:
            instance = self.docker.status(service)
            table_data = [
                _format_color('name', instance),
                _format_color('status', instance)
            ]
            if self.show_git:
                table_data.append(self.git.status(service))
            if self.show_port == 'column':
                table_data.append(instance.ports)
            for category in self.categories:
                table_data.append(self._get_service_category_data(service, category))
            table_lines.append(table_data)

        table = tabulate(table_lines, table_header)
        self._widget = dashing.Text(table, color=6, border_color=5, title=self.title)

    def _get_service_category_data(self, service: str, category: str) -> str:
        pass


def _format_color(field, instance):
    func = getattr(instance.format, formatStr)
    return func(getattr(field, instance), use_prefix=False)










