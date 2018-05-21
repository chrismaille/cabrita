"""Box Module.

This module has the Box Class, which is the building block for dashboards.

Each box updates his data in a separate thread in Python.
"""
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
    """Update box data.

    This method are called by a thread class to update.
    :param box: the box to update
    :return: dashing object
    """
    try:
        box.run()
        return box.widget
    except Exception:
        client = get_sentry_client()
        if client:
            client.captureException()
        raise


class Box:
    """Box Class.

    The building block of the dashboard.

    This class is called inside the CabritaCommand class,
    using the data from Config and Compose classes.
    """

    def __init__(self, background_color: BoxColor = BoxColor.black, compose: Compose = None, git: GitInspect = None,
                 docker: DockerInspect = None) -> None:
        """Init class."""
        self.last_update = datetime.now()
        self.data = {}
        self.compose = compose
        self.git = git
        self.docker = docker
        self._background_color = background_color.value
        self._services = []
        self.data_inspected_from_service = {}
        self._widget = dashing.Text("Fetching data...", color=6, border_color=5,
                                    background_color=background_color.value)

    @property
    def can_update(self) -> bool:
        """Check if box data can be updated.

        :return: bool
        """
        seconds_elapsed = (datetime.now() - self.last_update).total_seconds()
        return seconds_elapsed >= self.interval

    @property
    def widget(self) -> object:
        """Return dashing widget object.

        :return: dashing object
        """
        return self._widget

    @widget.setter
    def widget(self, value) -> None:
        self._widget = value

    @property
    def services(self) -> list:
        """Return unique sorted service names inside box.

        :return: list
        """
        return sorted(set(self._services))

    @services.setter
    def services(self, value):
        self._services = value

    @property
    def interval(self):
        """Return interval in seconds for each box data update.

        Minimum: 0.5.
        :return: float
        """
        return float(self.data.get('interval', 0.50))

    @property
    def show_git(self) -> bool:
        """Return if box will show git information (the 'show_git' box parameter).

        Default: True.
        :return: bool
        """
        return self.data.get('show_git', True)

    @property
    def show_revision(self) -> bool:
        """Return if box will show git tag/commit hash (the 'show_revision" box parameter).

        Default: False.
        :return:
        """
        return self.data.get('show_revision', False)

    @property
    def port_view(self) -> PortView:
        """Return if box will show docker container port info (the 'port_view' box parameter).

        Default: hidden.
        :return: PortView enum property.
        """
        return PortView(self.data.get('port_view', PortView.hidden))

    @property
    def port_detail(self) -> PortDetail:
        """Return if box will show external, internal or both docker container exposed ports.

        Works in conjunction with 'port_view' parameter. Default: external ports.
        :return: PortDetail enum property
        """
        return PortDetail(self.data.get('port_detail', PortDetail.external))

    @property
    def categories(self) -> List[str]:
        """Return if box will show services as columns (categories).

        Default: Show as lines.
        :return: list
        """
        return self.data.get('categories', [])

    @property
    def title(self) -> str:
        """Return box title name (the 'name' box parameter).

        Default: "Box".
        :return: string
        """
        return self.data.get('name', 'Box')

    @property
    def size(self) -> str:
        """Return box size to render in dashboard (the 'size' box parameter).

        Default: "large".
        :return: string
        """
        return self.data.get('size', 'large')

    @property
    def main(self) -> bool:
        """Return if this is the main box (the 'main' box parameter).

        Default: No
        Only one box can be true.
        :return: bool
        """
        return bool(self.data.get('main', False))

    @property
    def includes(self) -> list:
        """Return the list of the only services which will be included in this box.

        Default is: no filters.
        This option is mutually exclusive with the 'main' parameter.
        :return: list
        """
        return self.data.get('includes', [])

    @property
    def background_color(self) -> BoxColor:
        """Return the Box Color Enum.

        :return: BoxColor object
        """
        return self._background_color

    @background_color.setter
    def background_color(self, value: BoxColor):
        """Set the Background color for the box.

        :param value: BoxColor property
        :return: None
        """
        self._background_color = value.value

    def load_data(self, data: dict) -> None:
        """Add data from config class in box.

        :param data: config data parsed from cabrita.yml file.
        :return: None
        """
        self.data = data

    def add_service(self, service: str) -> None:
        """Append new service in box services list.

        :param service: service name
        :return: None
        """
        self._services.append(service)

    def _get_headers(self) -> List[str]:
        """Return the headers for box information.

        Always add Service and Status columns.
        Additional columns can be:
            - Git Revision Info (branch tag and commit hash)
            - Docker Container exposed ports
            - Git Branch Info (branch name and status)
            - categories listed in config yml for the box
        :return: list
        """
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
        """Append port info in field or just return field value.

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
        """Run main code for update box data.

        Updates the box widget property.
        :return: None
        """
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
                format_color(service_name, self.data_inspected_from_service['style'],
                             self.data_inspected_from_service['theme']),
                format_color(service_status, self.data_inspected_from_service['style'],
                             self.data_inspected_from_service['theme'])
            ]

            if self.show_revision:
                table_data.append(self.git.get_git_revision(service))

            if self.port_view == PortView.column:
                port_string = "" if not self.data_inspected_from_service['ports'] else self._append_ports_in_field(
                    "ports")
                table_data.append(format_color(port_string, self.data_inspected_from_service['style'],
                                               self.data_inspected_from_service['theme']))

            if self.show_git:
                table_data.append(self.git.status(service))

            for category in self.categories:
                category_data = self._get_service_category_data(striped_name, category)
                if not category_data:
                    table_data.append('--')
                else:
                    category_status = format_color(category_data['status'], category_data['style'],
                                                   category_data['theme'])
                    if self.port_view == PortView.status and category_data['ports'] and \
                            category_data['status'].lower() not in ["exited", "error", "not found"]:
                        category_status += ' {}'.format(category_data["ports"])
                    table_data.append(category_status)
            table_lines.append(table_data)

        if self.show_revision:
            table_lines = self.format_revision(table_lines)
        table = tabulate(table_lines, table_header)
        self._widget = dashing.Text(table, color=6, border_color=5, background_color=self.background_color,
                                    title=self.title)

    def _get_service_category_data(self, service: str, category: str) -> Optional[dict]:
        """Find the service name + category service in compose data and return inspect docker data.

        Example
        -------
            The service name is 'auth' and the category is 'worker'
            The code will attempt to find the 'auth-worker' service inside compose data.
            The Search are not case-sensitive and not will not match entire name. 'Auth-Worker1' will be found.
            If find, return the docker inspect data for this service.
        :param service: service name
        :param category: category name
        :return: dict or None
        """
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

    @staticmethod
    def format_revision(table_lines: list) -> list:
        """Format revision info to make all lines have the same width.

        Example:
            Revision 1: master@1234abc
            Revision 2: epic/refactoring@5678def

            After formatting:

            Revision 1:           master@1234abc
            Revision 2: epic/refactoring@5678def

        :param table_lines: list
        :return: list
        """
        largest_tag = max([
            len(line[2].split("@")[0] if "@" in line[2] else "")
            for line in table_lines
        ])

        new_lines = []
        for line in table_lines:
            tag = line[2].split("@")[0] if "@" in line[2] else ""
            tag = tag.ljust(largest_tag + 1)
            tag = formatStr.info(tag, use_prefix=False)
            commit_hash = line[2].split("@")[1] if "@" in line[2] else line[2]
            commit_hash = formatStr.info(commit_hash, use_prefix=False, theme="dark")
            revision = "{}{}".format(tag, commit_hash)
            line = [
                column if index != 2 else revision
                for index, column in enumerate(line)
            ]
            new_lines.append(line)

        return new_lines
