from unittest import TestCase, mock

from dashing import dashing

from cabrita.components import BoxColor
from cabrita.components.box import Box


class TestBox(TestCase):

    @mock.patch('cabrita.components.config.Compose')
    @mock.patch('cabrita.components.git.GitInspect')
    @mock.patch('cabrita.components.docker.DockerInspect')
    def setUp(self, *args):
        self.box = Box(
            compose=args[2],
            git=args[1],
            docker=args[0],
            background_color=BoxColor.black
        )

    def test_can_update(self):
        assert self.box.can_update is False

    def test_widget(self):
        assert isinstance(self.box.widget, dashing.Text)

    def test_interval(self):
        assert self.box.interval is not 0

    def test_show_git(self):
        assert isinstance(self.box.show_git, bool)
        assert self.box.show_git is True

    def test_show_revision(self):
        assert isinstance(self.box.show_revision, bool)
        assert self.box.show_revision is False

    def test_port_view(self):
        from cabrita.components.docker import PortView

        assert self.box.port_view is PortView.hidden

    def test_port_detail(self):
        from cabrita.components.docker import PortDetail

        assert self.box.port_detail is PortDetail.external

    def test_categories(self):
        assert isinstance(self.box.categories, list)

    def test_title(self):
        assert self.box.title == "Box"

    def test_size(self):
        assert self.box.size == "large"

    def test_main(self):
        assert self.box.main is not True
        assert isinstance(self.box.main, bool)

    def test_includes(self):
        assert isinstance(self.box.categories, list)

    def test_background_color(self):
        assert self.box.background_color == BoxColor.black.value

    def test_load_data(self):
        self.box.load_data(
            {
                'show_revision': True
            }
        )
        assert self.box.show_revision is True

    def test_add_service(self):
        self.box.add_service('django')
        assert len(self.box.services) == 1

    def test__get_headers(self):
        from cabrita.components.docker import PortView

        self.box.load_data(
            {
                'show_revision': True,
                'port_view': PortView.column,
                'categories': ['Web', 'Worker']
            }
        )
        test_headers = self.box._get_headers()
        self.assertEqual(test_headers, ['Service', 'Status', 'Revision', 'Port', 'Git', 'Web', 'Worker'])

    def test__add_ports(self):
        self.fail()

    def test_run(self):
        self.fail()

    def test__get_service_category_data(self):
        self.fail()

    def test_format_revision(self):
        self.fail()


class TestUpdate_box(TestCase):
    def test_update_box(self):
        self.fail()
