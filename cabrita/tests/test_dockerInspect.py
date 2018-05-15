from unittest import TestCase

from cabrita.command import CabritaCommand


class TestDockerInspect(TestCase):

    def setUp(self):
        command = CabritaCommand(
            cabrita_path='./examples/config/cabrita-v2.yml',
            compose_path=(),
            version='test'
        )
        self.assertTrue(command.has_a_valid_config)
        command.read_compose_files()
        self.assertTrue(command.has_a_valid_compose)
        command.prepare_dashboard()
        self.docker = command.dashboard.all_boxes[0].docker

    def test_inspect(self):
        self.fail()

    def test__get_service_ports(self):
        self.fail()

    def test__get_container_name(self):
        self.fail()

    def test__get_inspect_data(self):
        self.fail()

    def test__define_status(self):
        self.fail()

    def test__need_build(self):
        self.fail()
