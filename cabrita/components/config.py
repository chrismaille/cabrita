from typing import List, Union, Optional

from cabrita.abc.base import ConfigTemplate
from cabrita.abc.utils import get_path


def _check_v3() -> bool:
    """
    TODO: Validate data from cabrita.yml files
    :return:
        bool
    """
    return True


class Config(ConfigTemplate):
    """
    Cabrita Configuration main class.
    """

    @property
    def compose_files(self) -> List[str]:
        return self.data['compose_files']

    @property
    def layout(self) -> str:
        return self.data['layout']

    @property
    def boxes(self) -> List[dict]:
        return self.data['boxes']

    @property
    def interval(self) -> int:
        return int(self.data['interval'])

    @property
    def watchers(self) -> List[str]:
        return self.data['check_list']

    @property
    def is_valid(self) -> bool:
        if not self.data:
            raise ValueError("Data must be loaded before validation")

        version = int(self.data.get("version"))

        if not version:
            self.console.error("Configuration Version must be informed")
            return False

        if not hasattr(self, "_check_v{}".format(self.version)):
            self.console.error("Unknown configuration version")
            return False

        return getattr(self, "_check_v{}".format(self.version))

    def _check_v1(self) -> bool:
        return self._check_v2()

    def _check_v2(self) -> bool:
        self.console.error('This version is deprecated.  Please update to version 3.')
        return False

    def _check_v3(self) -> bool:
        """
        TODO: Validate data from cabrita.yml version 3 files
        :return:
            bool
        """
        return True


class Compose(ConfigTemplate):
    """
    Main class for Docker-Compose data.
    """

    @property
    def services(self) -> List[dict]:
        return self.data['services']

    @property
    def volumes(self) -> List[str]:
        return self.data['volumes']

    @property
    def networks(self) -> List[str]:
        return self.data['networks']

    @property
    def is_valid(self) -> bool:
        if not self.data:
            raise ValueError("Data must be loaded before validation")

        return self._check()

    def is_image(self, service_name: str) -> bool:
        """
        Check if service are built from image or dockerfile
        :param service_name:
            docker service name
        :return:
            bool
        """
        return False if self.get_from_service(service_name, 'build') else True

    def get_build_path(self, service_name: str) -> str:
        """
        Get build full path for service

        :param service_name:
            docker service name
        :return:
            str
        """
        data = self.get_from_service(service_name, 'build')
        path = data.get('context') if isinstance(data, dict) else data
        return get_path(path, self.base_path)

    def get_from_service(self, service_name: str, key: str) -> Optional[Union[dict, str, List]]:
        """
        Get value from key for informed service.

        Example: get_from_service("flower", "ports") returns ["5555"]

        :param service_name:
            docker service name
        :param key:
            search key for service data
        :return:
            List, String, Dict or None
        """
        service = [
            s
            for s in self.services
            if s == service_name
        ][0]
        return service.get(key, None)

    def _check(self) -> bool:
        """
        TODO: Validate docker-compose yaml files.
        :return:
            bool
        """
        return True