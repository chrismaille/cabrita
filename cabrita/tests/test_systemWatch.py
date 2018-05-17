from unittest import TestCase, mock

from cabrita.command import CabritaCommand
from cabrita.tests import LATEST_CONFIG_PATH

DOCKER_DF_DATA = \
"""
23.87GB
1.699GB
16.25GB
0B
"""

class TestSystemWatch(TestCase):

    def setUp(self):
        command = CabritaCommand(
            cabrita_path=LATEST_CONFIG_PATH,
            compose_path=(),
            version='test'
        )
        self.assertTrue(command.has_a_valid_config)
        command.read_compose_files()
        self.assertTrue(command.has_a_valid_compose)
        command.prepare_dashboard()
        self.watch = command.dashboard.system_watch

    @mock.patch('cabrita.components.watchers.run_command', return_value=DOCKER_DF_DATA)
    def test__get_docker_folder_size(self, *mocks):
        size = self.watch._get_docker_folder_size()
        self.assertEqual(size, 44902809337.856)

    @mock.patch('cabrita.components.watchers.run_command', return_value=DOCKER_DF_DATA)
    def test_run(self, *mocks):
        from dashing import dashing
        self.watch.run()
        self.assertIsInstance(self.watch.widget, dashing.VSplit)
