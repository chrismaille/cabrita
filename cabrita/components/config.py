from cabrita.abc.files import ConfigBase


class Config(ConfigBase):


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


