"""Config module.

This module has:
    The **Config class**, which is responsible for
    handling program options from cabrita.yml file.

    The **Compose class**, which is responsible for
    handling docker-compose data from yamls.
"""
import logging
import math
import os
import shutil
from typing import List, Optional, Any

from buzio import console

from cabrita.abc.base import ConfigTemplate
from cabrita.abc.utils import get_path
from cabrita.components import BoxColor

logger = logging.getLogger(__name__)


class Config(ConfigTemplate):
    """Cabrita Configuration main class."""

    @property
    def ignore_services(self) -> List[str]:
        """Return ignore services in dashboard.

        Parameter: 'ignore_services'.
        Default: All services viewed.

        :return: list
        """
        return self.data.get('ignore_services', [])

    @property
    def compose_files(self) -> List[str]:
        """Return docker-compose paths list.

        Parameter: 'compose_files'.
        Default is empty.

        :return: list
        """
        return self.data['compose_files']

    @property
    def layout(self) -> str:
        """Return dashboard layout.

        Parameter: 'layout'
        Options are: 'horizontal' and 'vertical'. Default: 'horizontal'.

        :return: str
        """
        return self.data['layout']

    @property
    def boxes(self) -> dict:
        """Return box configuration data.

        Parameter: 'boxes'.
        No default available.

        :return: dict
        """
        return self.data['boxes']

    @property
    def title(self) -> str:
        """Return dashboard title.

        Parameter: 'title'.
        Default: 'Docker-Compose'.

        :return: str
        """
        return self.data.get('title') or "Docker-Compose"

    @property
    def background_color(self) -> BoxColor:
        """Return background color for box.

        Parameter: 'background_color'.
        Options: Black, Blue, Cyan, Grey, Yellow, White.
        Default: Black.

        :return: BoxColor instance.
        """
        return getattr(BoxColor, self.data.get('background_color', 'black'))

    @property
    def background_color_value(self) -> int:
        """Return blessed box color value from enum.

        :return: int
        """
        return self.background_color.value

    @property
    def watchers(self) -> dict:
        """Return watchers configuration data.

        Parameter: 'watchers'.

        No default available.
        :return:
        """
        return self.data.get('watchers', {})

    @property
    def is_valid(self) -> bool:
        """Return if configuration is valid.

        Calls for the version founded inside yml file:
            Version 0: No yml available - calls _check_v0().
            Version 1: Deprecated - calls _check_v1().
            Version 2: Last version - calls _check_v2().

        :return: bool
        """
        if not hasattr(self, "_check_v{}".format(self.version)):
            self.console.error("Unknown configuration version")
            return False

        return getattr(self, "_check_v{}".format(self.version))(start_here=True)

    def _check_v0(self, start_here: bool = False) -> bool:
        """Check for version 0.

        This version are called when user do not inform any yaml file.

        :param start_here: Check if operation starts here, to show message.

        :return: bool
        """
        if start_here:
            self.console.info('Autogenerated Boxes using default configuration.')

        self.data['layout'] = "horizontal"
        if self.manual_compose_paths:
            self.data['compose_files'] = self.manual_compose_paths

        return self._check_v1()

    def _check_v1(self, start_here: bool = False) -> bool:
        """Check for version 1.

        Deprecated Version. This version use only on docker-compose.yml file.

        :param start_here: Check if operation starts here, to show message.

        :return: bool
        """
        if start_here:
            self.console.warning(
                'Version 1 for configuration is outdated. Please update your config file to version 2.')

        if self.manual_compose_paths:
            self.data['compose_files'] = self.manual_compose_paths
        else:
            if self.data.get('docker-compose') and (
                    'path' not in self.data.get('docker-compose').keys() or
                    'name' not in self.data.get('docker-compose').keys()):
                self.console.error('Key "docker-compose" must have "name" and "path" parameters')
                return False
            docker_compose_data = self.data.pop('docker-compose', {})
            docker_compose_path = []  # type: List[str]
            if docker_compose_data:
                docker_compose_path = [os.path.join(docker_compose_data['path'], docker_compose_data['name'])]
            self.data['compose_files'] = docker_compose_path

        ignore_list = self.data.pop('ignore', [])
        if ignore_list:
            self.data['ignore_services'] = ignore_list

        watch_files_dict = self.data.pop('files', {})
        ping_ngrok = self.data.get('check', {}).get('ngrok', False)
        if watch_files_dict or ping_ngrok:
            self.data['watchers'] = {}
            if watch_files_dict:
                self.data['watchers']['file_watch'] = watch_files_dict
            if ping_ngrok:
                self.data['watchers']['ping'] = {
                    "ngrok": {
                        "name": "Ngrok Access",
                        "address": "http://localhost:4040",
                        "message_on_success": "UP",
                        "message_on_error": "DOWN"
                    }
                }

        if self.data.get('box'):
            self.data['boxes'] = {}
            for box_name in self.data['box']:
                old_data = self.data['box'][box_name]
                new_data = {}
                if old_data.get('catch_all'):
                    new_data['main'] = True
                if old_data.get('name'):
                    new_data['name'] = old_data.get('name')
                if old_data.get('size'):
                    new_data['size'] = old_data.get('size')
                if old_data.get('target_branch'):
                    new_data['watch_branch'] = old_data['target_branch']
                if old_data.get('show_ports'):
                    new_data['port_view'] = old_data['show_ports']
                if old_data.get('list_only'):
                    new_data['includes'] = old_data['list_only']
                if old_data.get('categories'):
                    new_data['categories'] = old_data['categories']
                if self.data.get('build_check'):
                    new_data['watch_for_build_using_files'] = self.data.get('build_check')
                if self.data.get('build_check_using_git'):
                    new_data['watch_for_build_using_git'] = self.data.get('build_check_using_git')
                self.data['boxes'][box_name] = new_data

            self.data.pop('box')

        return self._check_v2()

    def _check_v2(self, start_here: bool = False) -> bool:
        """Check for version 2. Latest version.

        :param start_here: Check if operation starts here, to show message.

        :return: bool
        """
        if start_here:
            self.console.info('Validating configuration data...')

        if self.manual_compose_paths:
            self.data['compose_files'] = self.manual_compose_paths

        ret = True

        if self.data.get('layout') and self.data.get('layout') not in ['horizontal', 'vertical']:
            self.console.error('Layout must be vertical or horizontal')
            ret = False

        if self.data.get('background_color') and self.data.get('background_color') not in BoxColor.__members__:
            self.console.error('Valid background colors are: {}'.format(", ".join(sorted(BoxColor.__members__))))
            ret = False

        if not self.data.get('compose_files'):
            self.console.error('You must inform at least one Docker-Compose file path.')
            ret = False
        elif not isinstance(self.data.get('compose_files'), list):
            self.console.error('Docker-Compose files must be a list')
            ret = False

        if self.data.get('ignore_services') is not None and not isinstance(self.data.get('ignore_services'), list):
            self.console.error('Ignore Services must be a list')
            ret = False

        if self.data.get('boxes'):
            # Check for more than one main box
            main_box_count = [
                box_name
                for box_name in self.data['boxes']
                if self.data['boxes'].get(box_name).get('main')
            ]
            if len(main_box_count) > 1:
                self.console.error('Only one box must have the "main" parameter')
                ret = False
            if len(main_box_count) == 0:
                self.console.error('No box have the "main" parameter')
                ret = False
            if len(main_box_count) == 1:
                main_box = self.data['boxes'][main_box_count[0]]
                if main_box.get('includes') is not None:
                    self.console.error('Box with "main" parameter must do not contain "includes"')
                    ret = False

        for box_name in self.data.get('boxes', {}):
            data_in_box = self.data['boxes'][box_name]
            if data_in_box.get('size') and data_in_box.get('size') not in ['big', 'small']:
                self.console.error('Size for Box "{}" must be "big" or "small"'.format(box_name))
                ret = False
            if data_in_box.get('port_view') and data_in_box.get('port_view') not in ['column', 'name', 'status']:
                self.console.error(
                    'Port View in Box "{}" must be "column", "name" or "status". Value is: {}'.format(box_name,
                                                                                                      data_in_box[
                                                                                                          'port_view']))
                ret = False
            if data_in_box.get('port_detail') and data_in_box.get('port_detail') not in ['external', 'internal',
                                                                                         'both']:
                self.console.error('Port Detail in Box "{}" must be "external", "internal" or "both".'.format(box_name))
                ret = False
            if data_in_box.get('includes') is not None and not isinstance(data_in_box.get('includes'), list):
                self.console.error('Include in Box "{}" must be a list'.format(box_name))
                ret = False
            if data_in_box.get('categories') is not None and not isinstance(data_in_box.get('categories'), list):
                self.console.error('Categories in Box "{}" must be a list'.format(box_name))
                ret = False
            if self.data.get('watch_for_build_using_files') is not None:
                if not isinstance(self.data.get('watch_for_build_using_files'), list):
                    self.console.error('Watch for Build using Files Check must be a list')
                    ret = False
            if self.data.get('watch_for_build_using_git') is not None:
                if not isinstance(self.data.get('watch_for_build_using_git'), list):
                    self.console.error('Watch for Build using Git Check must be a list')
                    ret = False

        return ret

    @staticmethod
    def get_compose_path(compose_path: str, base_path: str) -> str:
        """Get docker-compose file full path.

        The compose path can be absolute or relative - the 'base_path' will
        be used to resolve full path.

        :param compose_path: the path for docker-compose file.

        :param base_path: the base path for cabrita.yml file.

        :return: str
        """
        return get_path(compose_path, base_path)

    def generate_boxes(self, services: dict):
        """Autogenerate boxes in version 0 runs.

        The number of boxes are determined by terminal size.
        The columns visible inside each one are determined
        by the number of boxes generated.

        :param services: services to be included in dashboard.

        :return: dict
        """
        service_list = sorted(list(services.keys()))
        self.data['boxes'] = {}

        columns, lines = shutil.get_terminal_size()
        max_services_per_box = lines - 10
        num_of_boxes = int(math.ceil(len(service_list) / max_services_per_box)) or 1
        logger.debug("Number of Boxes: {}".format(num_of_boxes))
        i = 0
        for box_num in range(num_of_boxes):
            services_in_box = []  # type: List[str]
            while len(services_in_box) <= max_services_per_box and i <= len(service_list) - 1:
                services_in_box.append(service_list[i])
                i += 1
            if services_in_box:
                self.data['boxes']["box_{}".format(box_num)] = {
                    "name": "Docker Services",
                    "size": "small",
                    "port_view": "column" if num_of_boxes <= 4 else "name",
                    "includes": services_in_box
                }
                if num_of_boxes <= 2:
                    self.data['boxes']["box_{}".format(box_num)]['show_revision'] = True


class Compose(ConfigTemplate):
    """Main class for Docker-Compose data."""

    @property
    def services(self) -> dict:
        """Return services configuration in docker-compose yaml files.

        :return: dict
        """
        return self.data['services']

    @property
    def volumes(self) -> dict:
        """Return volumes configuration in docker-compose yaml files.

        :return: dict
        """
        return self.data['volumes']

    @property
    def networks(self) -> dict:
        """Return networks configuration in docker-compose yaml files.

        :return: dict
        """
        return self.data['networks']

    @property
    def is_valid(self) -> bool:
        """Return if docker-compose are valid.

        :return: bool
        """
        if not self.list_path:
            raise ValueError("Data must be loaded before validation")

        return self._check()

    def is_image(self, service_name: str) -> bool:
        """Check if service are built from image or dockerfile.

        :param service_name:
            docker service name

        :return:
            bool
        """
        return False if self.get_from_service(service_name, 'build') else True

    def get_build_path(self, service_name: str) -> str:
        """Get build full path for service.

        :param service_name:
            docker service name

        :return:
            str
        """
        data = self.get_from_service(service_name, 'build')
        path = data.get('context') if isinstance(data, dict) else data
        return get_path(path, self.base_path)

    def get_from_service(self, service_name: str, key: str) -> Any:
        """Get value from key for informed service.

        Example: get_from_service("flower", "ports") returns ["5555"]

        :param service_name:
            docker service name

        :param key:
            search key for service data

        :return:
            List, String, Dict or None
        """
        service = [
            self.data['services'][s]
            for s in self.services
            if service_name.lower() == s
        ][0]
        return service.get(key, None)

    def get_ports_from_service(self, service: str) -> Optional[List]:
        """Return ports from service.

        The ports can be from the 'ports' or 'expose' parameters in yaml.

        :param service: service name

        :return: List or None
        """
        port_data = self.get_from_service(service, 'ports')
        if not port_data:
            port_data = self.get_from_service(service, 'expose')
        return port_data

    def _check(self) -> bool:
        """Check if yml is valid.

        :return:
            bool
        """
        path, base_path = self.list_path[-1]
        if 'override' in path:
            return True
        command = "cd {} && docker-compose config".format(
            os.path.dirname(get_path(path, base_path))
        )
        ret = console.run(command, get_stdout=False, silent=True)
        if not ret:
            console.run(command)
        return ret
