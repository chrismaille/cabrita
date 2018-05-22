import os
from pathlib import Path
from unittest import TestCase

from cabrita.components.config import Config


class TestConfig(TestCase):

    def setUp(self):
        self.maxDiff = None
        self._generate_config()

    def _generate_config(self):
        self.config = Config()
        self.config.add_path('./examples/config/cabrita-v1.yml')
        self.config.load_file_data()
        self.assertTrue(self.config.is_valid)

    def test_ignore_services(self):
        self.assertListEqual(self.config.ignore_services, ['portainer'])

    def test_compose_files(self):
        self.assertListEqual(self.config.compose_files, ['$TEST_PROJECT_PATH/docker-compose.yml'])

    def test_layout(self):
        self.assertEqual(self.config.layout, 'horizontal')

    def test_boxes(self):
        self.assertEqual(len(self.config.boxes.keys()), 3)
        for box_name in self.config.boxes.keys():
            self.assertTrue(box_name in ['all', 'workers', 'devops'])

    def test_title(self):
        self.assertEqual(self.config.title, "Docker-Compose")

    def test_background_color(self):
        from cabrita.components import BoxColor
        self.assertEqual(self.config.background_color, BoxColor.black)

    def test_background_color_value(self):
        self.assertEqual(self.config.background_color_value, 16)

    def test_watchers(self):
        pass

    def test_get_compose_path(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = str(Path(current_dir).parent.parent)
        os.environ['TEST_PROJECT_PATH'] = os.path.join(parent_dir, 'examples')
        self.assertEqual(
            Path(self.config.get_compose_path('$TEST_PROJECT_PATH/docker-compose.yml', parent_dir)),
            Path(os.path.join(parent_dir, 'examples/docker-compose.yml')).resolve()
        )

    def test_generate_boxes(self):
        services_list = {'django': {}, 'django-worker': {}, 'flask': {}}
        expected_box = {
            'box_0': {
                'includes': ['django', 'django-worker', 'flask'],
                'name': 'Docker Services',
                'port_view': 'column',
                'show_revision': True,
                'size': 'small'
            }
        }
        self.config.generate_boxes(services_list)
        self.assertDictEqual(self.config.boxes, expected_box)
