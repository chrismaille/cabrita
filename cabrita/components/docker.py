import datetime
import json
import os
import re
import time
from enum import Enum
from typing import List, Tuple, Optional

from tzlocal import get_localzone

from cabrita.abc.base import InspectTemplate
from cabrita.abc.utils import get_path
from cabrita.components.config import Compose

IN = u"↗"
OUT = u"↘"
BOTH = u"⇄"


class PortDetail(Enum):
    external = "external"
    internal = "internal"
    both = "both"


class PortView(Enum):
    hidden = "hidden"
    column = "column"
    name = "name"
    status = "status"


class DockerInspect(InspectTemplate):

    def __init__(self, compose: Compose, interval: int, port_view: PortView, port_detail: PortDetail,
                 files_to_watch: List[str], services_to_check_git: List[str]) -> None:
        super(DockerInspect, self).__init__(compose, interval)
        self.port_view = PortView(port_view)
        self.port_detail = PortDetail(port_detail)
        self.files_to_watch = files_to_watch
        self.services_to_check_git = services_to_check_git
        self.default_data = {
            'name': "Fetching...",
            'status': "Fetching...",
            'format': 'dark',
            'ports': ""
        }

    def inspect(self, service: str) -> None:
        container_name = self._get_container_name(service)
        inspect_data = self._get_inspect_data(container_name)

        if not inspect_data:
            service_status = "Not Found"
            text_style = "info"
            text_theme = "dark"
        elif self._need_build(service, inspect_data):
            service_status = "NEED BUILD"
            text_style = "error"
            text_theme = None
        else:
            service_status, text_style, text_theme = self._define_status(inspect_data)


        self._status[service] = {
            "name": service,
            "status": service_status,
            "style": text_style,
            "theme": text_theme,
            "ports": self._get_service_ports(service)
        }

    def _get_service_ports(self, service: str) -> str:
        internal_ports = []
        external_ports = []
        port_list = self.compose.get_from_service(service, 'ports') or ""

        if not port_list:
            return ""

        for port in port_list:
            if ":" in port:
                external_ports.append(f"{port.split(':')[0]}")
                internal_ports.append(f"{port.split(':')[-1]}")
            else:
                internal_ports.append(f"{port}")

        if internal_ports == external_ports:
            return f'{BOTH} {" ".join(external_ports)}'

        if self.port_detail == PortDetail.external:
            service_string = f'{OUT} {" ".join(external_ports)}'
        elif self.port_detail == PortDetail.internal:
            service_string = f'{IN} {" ".join(internal_ports)}'
        else:
            service_string = f'{OUT} {" ".join(external_ports)} {IN} {" ".join(internal_ports)}'

        return service_string

    def _get_container_name(self, service: str) -> str:
        # Try container_name first
        name = self.compose.get_from_service(service, 'container_name')
        if not name:
            # Generate default_name
            name = os.path.basename(os.path.dirname(self.compose.full_path))
            name = re.sub(r'[^A-Za-z0-9]+', '', name)
            name = f"{name}_{service}_1"
        return name

    def _get_inspect_data(self, service: str) -> dict:
        ret = self.run(
            'docker inspect {} 2>/dev/null'.format(service),
            get_stdout=True
        )
        return json.loads(ret)[0] if ret else {}

    def _define_status(self, inspect_data) -> Tuple[str, str, Optional[str]]:
        theme = None
        if not inspect_data.get('State'):
            return "Error", "error", None
        if inspect_data['State'].get('Health', False):
            if inspect_data['State']['Status'].lower() == 'running':
                stats = inspect_data['State']['Health']['Status'].title()
            else:
                stats = inspect_data['State']['Status'].title()
            if inspect_data['State']['Running']:
                if inspect_data['State']['Health']['Status'] == 'healthy':
                    style = "success"
                else:
                    if inspect_data['State']['Health']['FailingStreak'] > 3:
                        style = "error"
                    else:
                        style = "warning"
            elif inspect_data['State']['Paused']:
                style = "warning"
            elif not inspect_data['State']['Running']:
                style = "info"
                theme = "dark"
            else:
                style = "error"
        else:
            stats = inspect_data['State']['Status'].title()
            if inspect_data['State']['Running']:
                style = "success"
            elif inspect_data['State']['Paused']:
                style = "warning"
            elif not inspect_data['State']['Running']:
                style = "info"
                theme = "dark"
            else:
                style = "error"

        return stats, style, theme

    def _need_build(self, service: str, inspect_data: dict) -> bool:
        test_date = None
        image_name = inspect_data['Config']['Image']
        image_data = self.run(
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

        label = inspect_data['Config']['Labels'].get('com.docker.compose.service')
        if not label:
            return False
        full_path = None
        if test_date and self.compose.get_from_service(label, 'build'):
            build_path = self.compose.get_from_service(label, 'build')
            if isinstance(build_path, dict):
                build_path = build_path.get('context')
            full_path = get_path(build_path, self.compose.base_path)
            list_dates = [
                datetime.datetime.fromtimestamp(
                    os.path.getmtime(os.path.join(full_path, file)),
                    tz=get_localzone()
                )
                for file in self.files_to_watch
                if os.path.isfile(os.path.join(full_path, file))
            ]
            if list_dates:
                if max(list_dates) > test_date:
                    return True

        # Check for build using commit
        # Ex.: 2018-02-23 18:31:45 -0300
        if service in self.services_to_check_git and full_path:
            git_log = self.run(
                'cd {} && git log -1 --pretty=format:"%cd" --date=iso'.format(full_path),
                get_stdout=True
            )
            date_fmt = "%Y-%m-%d %H:%M:%S %z"
            if git_log:
                commit_date = datetime.datetime.strptime(git_log, date_fmt)
                if commit_date > test_date:
                    return True

        return False
