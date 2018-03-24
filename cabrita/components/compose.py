from cabrita.abc.files import ConfigBase


class Compose(ConfigBase):

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

    def _check(self):

        return True
