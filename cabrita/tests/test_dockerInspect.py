import json
from unittest import TestCase, mock

from cabrita.command import CabritaCommand
from cabrita.tests import INSPECT_DJANGO_CONTAINER, INSPECT_DJANGO_IMAGE


class TestDockerInspect(TestCase):

    @mock.patch('cabrita.abc.utils.run_command', return_value=INSPECT_DJANGO_CONTAINER)
    def setUp(self, *mocks):
        command = CabritaCommand(
            cabrita_path='./examples/config/cabrita-v2.yml',
            compose_path=(),
            version='test'
        )
        self.assertTrue(command.has_a_valid_config)
        command.read_compose_files()
        self.assertTrue(command.has_a_valid_compose)
        command.prepare_dashboard()
        self.docker = command.dashboard.all_boxes[-1].docker

    def test_inspect(self):
        result_dict = {
            'name': 'django',
            'ports': '↘ 8081 8090',
            'status': 'Running',
            'style': 'success',
            'theme': None
        }
        self.docker.inspect('django')
        self.assertDictEqual(self.docker.status('django'), result_dict)

    def test__get_service_ports(self):
        test_ports = self.docker._get_service_ports('django')
        self.assertEqual(test_ports, u'↘ 8081 8090')

    def test__get_container_name(self):
        test_name = self.docker._get_container_name('django')
        self.assertEqual(test_name, 'examples_django_1')

    def test__get_inspect_data(self):
        test_name = self.docker._get_container_name('django')
        test_data = self.docker._get_inspect_data(test_name)
        self.assertEqual(test_data, json.loads(INSPECT_DJANGO_CONTAINER)[0])

    def test__define_status(self):
        test_name = self.docker._get_container_name('django')
        test_data = self.docker._get_inspect_data(test_name)
        test_stats, test_style, test_theme = self.docker._define_status(test_data)
        self.assertEqual(test_stats, 'Running')
        self.assertEqual(test_style, 'success')
        self.assertEqual(test_theme, None)

    @mock.patch('cabrita.abc.utils.run_command', return_value=INSPECT_DJANGO_IMAGE)
    def test__need_build(self, *mocks):
        service_name = 'django'
        test_name = self.docker._get_container_name(service_name)
        test_data = self.docker._get_inspect_data(test_name)
        self.docker.run = mocks[0]
        self.assertFalse(self.docker._need_build(service_name, test_data))
