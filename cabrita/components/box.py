from datetime import datetime
from typing import List, Optional

from buzio import formatStr
from dashing import dashing
from tabulate import tabulate

from cabrita.abc.utils import format_color, get_sentry_client
from cabrita.components import BoxColor
from cabrita.components.config import Compose
from cabrita.components.docker import DockerInspect, PortView, PortDetail
from cabrita.components.git import GitInspect


def update_box(box):
    try:
        box.run()
        return box.widget
    except Exception:
        client = get_sentry_client()
        if client:
            client.captureException()
        raise


class Box:

    def __init__(self, background_color: BoxColor = BoxColor.black, compose: Compose = None, git: GitInspect = None,
                 docker: DockerInspect = None) -> None:
        self.last_update = datetime.now()
        self.data = {}
        self.compose = compose
        self.git = git
        self.docker = docker
        self.background_color = background_color
        self._services = []
        self.data_inspected_from_service = {}
        self._widget = dashing.Text("Fetching data...", color=6, border_color=5,
                                    background_color=background_color.value)

    @property
    def can_update(self) -> bool:
        seconds_elapsed = (datetime.now() - self.last_update).total_seconds()
        return seconds_elapsed >= self.interval

    @property
    def widget(self) -> object:
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
        return float(self.data.get('interval', 0.50))

    @property
    def show_git(self) -> bool:
        return self.data.get('show_git', True)

    @property
    def show_revision(self) -> bool:
        return self.data.get('show_revision', False)

    @property
    def port_view(self) -> PortView:
        return PortView(self.data.get('port_view', PortView.hidden))

    @property
    def port_detail(self) -> PortDetail:
        return PortDetail(self.data.get('port_detail', PortDetail.external))

    @property
    def categories(self) -> List[str]:
        return self.data.get('categories', [])

    @property
    def title(self) -> str:
        return self.data.get('name', 'Box')

    @property
    def size(self) -> str:
        return self.data.get('size', 'large')

    @property
    def main(self) -> bool:
        return bool(self.data.get('main', False))

    @property
    def includes(self):
        return self.data.get('includes', [])

    @property
    def background_color(self):
        return self._background_color

    @background_color.setter
    def background_color(self, value: BoxColor):
        self._background_color = value.value

    def load_data(self, data: dict) -> None:
        self.data = data

    def add_service(self, service):
        self._services.append(service)

    def _get_headers(self) -> List[str]:
        table_header = ['Service', 'Status']
        if self.show_revision:
            table_header += ['Revision']
        if self.port_view == PortView.column:
            table_header += ['Port']
        if self.show_git:
            table_header += ['Git']
        if self.categories:
            table_header += self.categories
        return table_header

    def _append_ports_in_field(self, field) -> str:
        """
        Append port info in field or just return field value.
        :param field: str
            name field to append port info ('name' or 'status')
        :return:
            field value with or without port info (str)
        """
        if not self.data_inspected_from_service['ports']:
            return self.data_inspected_from_service[field]

        if self.data_inspected_from_service['status'].lower() in ["exited", "error", "not found", "need build"]:
            return self.data_inspected_from_service[field] if field != "ports" else ""

        if self.port_view == PortView.column:
            return self.data_inspected_from_service[field]

        if field != self.port_view.value:
            return self.data_inspected_from_service[field]
        else:
            return "{} ({})".format(self.data_inspected_from_service[field], self.data_inspected_from_service["ports"])

    def run(self) -> None:
        # Define Headers
        table_header = self._get_headers()

        # Get Services for Lines
        table_lines = []
        main_category = None
        striped_name = None
        if self.includes and self.categories:
            main_category = self.includes[0].lower()
            services_in_line = [
                s
                for s in self.services
                if main_category in s
            ]
        else:
            services_in_line = self.services

        for service in services_in_line:
            if main_category:
                striped_name = service.replace(main_category, "").replace("-", "").replace("_", "")

            self.data_inspected_from_service = self.docker.status(service)

            service_name = self._append_ports_in_field("name")
            service_status = self._append_ports_in_field("status")

            table_data = [
                format_color(service_name, self.data_inspected_from_service['style'], self.data_inspected_from_service['theme']),
                format_color(service_status, self.data_inspected_from_service['style'], self.data_inspected_from_service['theme'])
            ]

            if self.show_revision:
                table_data.append(self.git.get_git_revision(service))

            if self.port_view == PortView.column:
                port_string = "" if not self.data_inspected_from_service['ports'] else self._append_ports_in_field("ports")
                table_data.append(format_color(port_string, self.data_inspected_from_service['style'], self.data_inspected_from_service['theme']))

            if self.show_git:
                table_data.append(self.git.status(service))

            for category in self.categories:
                category_data = self._get_service_category_data(striped_name, category)
                if not category_data:
                    table_data.append('--')
                else:
                    category_status = format_color(category_data['status'], category_data['style'],
                                                   category_data['theme'])
                    if self.port_view == PortView.status and category_data['ports'] and category_data[
                        'status'].lower() not in ["exited", "error", "not found"]:
                        category_status += ' {}'.format(category_data["ports"])
                    table_data.append(category_status)
            table_lines.append(table_data)

        if self.show_revision:
            table_lines = self.format_revision(table_lines)
        table = tabulate(table_lines, table_header)
        self._widget = dashing.Text(table, color=6, border_color=5, background_color=self.background_color,
                                    title=self.title)

    def _get_service_category_data(self, service: str, category: str) -> Optional[dict]:
        service_to_find = [
            s
            for s in self.compose.services
            if service.lower() in s and category.lower() in s
        ]
        if service_to_find:
            service_data = self.docker.status(service_to_find[0])
            return service_data
        else:
            return None

    def format_revision(self, table_lines):

        largest_tag = max([
            len(line[2].split("@")[0] if "@" in line[2] else "")
            for line in table_lines
        ])

        new_lines = []
        for line in table_lines:
            tag = line[2].split("@")[0] if "@" in line[2] else ""
            tag = tag.ljust(largest_tag + 1)
            tag = formatStr.info(tag, use_prefix=False)
            hash = line[2].split("@")[1] if "@" in line[2] else line[2]
            hash = formatStr.info(hash, use_prefix=False, theme="dark")
            revision = "{}{}".format(tag, hash)
            line = [
                column if index != 2 else revision
                for index, column in enumerate(line)
            ]
            new_lines.append(line)

        return new_lines
