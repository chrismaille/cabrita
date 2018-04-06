from cabrita.abc.base import ConfigTemplate
from cabrita.abc.utils import get_path

class Config(ConfigTemplate):


    @property
    def compose_files(self):
        return self.data['compose_files']

    @property
    def layout(self):
        return self.data['layout']

    @property
    def boxes(self):
        return self.data['boxes']

    @property
    def interval(self):
        return int(self.data['interval'])

    @property
    def check_list(self):
        return self.data['check_list']

    @property
    def action_list(self):
        return self.data['action_list']

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


    def _check_v1(self):

        return True


class Compose(ConfigTemplate):

    @property
    def services(self):
        return self.data['services']

    @property
    def volumes(self):
        return self.data['volumes']

    @property
    def networks(self):
        return self.data['networks']

    @property
    def is_valid(self) -> bool:

        if not self.data:
            raise ValueError("Data must be loaded before validation")

        return self._check()

    def is_image(self, service_name):
        return False if self.get_from_service(service_name, 'build') else True

    def get_build_path(self, service_name: str) -> str:
        data = self.get_from_service(service_name, 'build')
        path = data.get('context') if isinstance(data, dict) else data
        return get_path(path, self.base_path)

    def get_from_service(self, service_name, key):
        return self.services.get(service_name).get(key, '')

    def _check(self):

        return True