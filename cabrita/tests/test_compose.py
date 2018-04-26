import os
from pathlib import Path
from unittest import TestCase

import yaml

from cabrita.components.config import Compose
from cabrita.tests import COMPOSE_YAML


class TestCompose(TestCase):

    def setUp(self):
        self.compose = Compose()
        self.compose.data = yaml.load(COMPOSE_YAML)

    def test_services(self):
        compose_list = [
            key
            for key in self.compose.services
            if isinstance(self.compose.services[key], dict)
        ]
        self.assertTrue(compose_list == ['django', 'django-worker', 'postgres'])

    def test_volumes(self):
        self.assertDictEqual(self.compose.volumes, {'postgres-data': None})

    def test_networks(self):
        self.assertDictEqual(self.compose.networks, {'backend': {'driver': 'bridge'}})

    def test_is_valid(self):
        self.compose.data = {}
        with self.assertRaises(ValueError):
            ret = self.compose.is_valid

    def test_is_image(self):
        self.assertTrue(self.compose.is_image('django-worker'))
        self.assertFalse(self.compose.is_image('django'))

    def test_get_build_path(self):
        full_path = self.compose.get_build_path('django')
        self.assertEqual(full_path, os.path.join(Path.home(), 'Projects'))

    def test_get_from_service(self):
        environment_list = self.compose.get_from_service('django', 'environment')
        self.assertEqual(environment_list[0].split("=")[0], 'DEBUG')


