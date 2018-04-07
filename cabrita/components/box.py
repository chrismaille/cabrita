from datetime import datetime
from threading import Thread
from typing import List

from dashing import dashing
from tabulate import tabulate
from buzio import formatStr

from cabrita.components.config import Compose
from cabrita.components.docker import DockerInspect
from cabrita.components.git import GitInspect


class Box(Thread):

    git: GitInspect = None
    compose: Compose = None
    docker: DockerInspect = None

    def __init__(self) -> None:
        super(Box, self).__init__()
        self._widget = ""
        self.last_update = datetime.now()
        self.data = {}

    @property
    def can_update(self) -> bool:
        seconds_elapsed = (datetime.now() - self.last_update).total_seconds()
        return seconds_elapsed >= self.interval

    @property
    def widget(self) -> str:
        if self.can_update:
            self.run()
        return self._widget

    @widget.setter
    def widget(self, value) -> None:
        self._widget = value


    @property
    def services(self):
        return sorted(set(self._services))

    @services.setter
    def services(self, value):
        self._services = value

    @property
    def interval(self):
        return int(self.data.get('interval', 0))

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

    @property
    def size(self) -> str:
        return self.data.get('size', 'large')

    @property
    def main(self) -> bool:
        return bool(self.data.get('main', False))

    def load_data(self, data: dict) -> None:
        self.data = data

    def add_service(self, service):
        self.services.append(service)

    def run(self) -> None:
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
            service_data = self.docker.status(service)
            if self.show_port == 'name':
                service_name = f'{service_data["name"]} ({service_data["ports"]})'
            else:
                service_name = service_data['name']
            table_data = [
                _format_color(service_name, service_data['format']),
                _format_color(service_data['status'], service_data['format'])
            ]
            if self.show_git:
                table_data.append(self.git.status(service))
            if self.show_port == 'column':
                table_data.append(service_data['ports'])
            for category in self.categories:
                table_data.append(self._get_service_category_data(service, category))
            table_lines.append(table_data)

        table = tabulate(table_lines, table_header)
        self._widget = dashing.Text(table, color=6, border_color=5, title=self.title)

    def _get_service_category_data(self, service: str, category: str) -> str:
        service_to_find = [
            s
            for s in self.compose.services
            if service in s and category in s
        ]
        if service_to_find:
            service_data = self.docker.status(service_to_find[0])
            return service_data['status']
        else:
            return "--"


def _format_color(field: str, string_format: str) -> str:
    func = getattr(formatStr, string_format)
    return func(field, use_prefix=False)
