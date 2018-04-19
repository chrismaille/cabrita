from unittest import TestCase, mock

from dashing import dashing

from cabrita.components import BoxColor
from cabrita.components.box import Box
from cabrita.components.docker import PortView


class TestBox(TestCase):

    def return_docker_status(self, service):
        mock_dict = {
            'django': {
                'ports': u'↘ 8081',
                'status': 'Running',
                'name': 'django',
                'style': 'success',
                'theme': None
            },
            'django-worker': {
                'ports': u'↘ 8085',
                'status': 'Running',
                'name': 'django-worker',
                'style': 'success',
                'theme': None
            },
        }
        return mock_dict[service]

    def return_revision_status(self, service):
        mock_dict = {
            'django': u"✎ 1.0.0@⑂ abcd12345",
            'django-worker': '--'
        }
        return mock_dict[service]

    def return_git_status(self, service):
        mock_dict = {
            'django': 'master ↓ 1',
            'django-worker': 'Using Image'
        }
        return mock_dict[service]

    @mock.patch('cabrita.components.config.Compose')
    @mock.patch('cabrita.components.git.GitInspect')
    @mock.patch('cabrita.components.docker.DockerInspect')
    def setUp(self, *args):

        docker_mock = args[0]
        docker_mock.status.side_effect = self.return_docker_status

        git_mock = args[1]
        git_mock.get_git_revision.return_value = self.return_revision_status
        git_mock.status.return_value = self.return_git_status

        self.box = Box(
            compose=args[2],
            git=git_mock,
            docker=docker_mock,
            background_color=BoxColor.black
        )
        self.box.load_data(
            {
                'show_revision': True,
                'port_view': PortView.column,
                'categories': ['Worker'],
                'includes': ['worker'],
            }
        )
        self.box.services = ['django', 'django-worker']

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
        assert self.box.show_revision is True

    def test_add_service(self):
        self.box.add_service('django')
        assert len(self.box.services) == 1

    def test__get_headers(self):
        test_headers = self.box._get_headers()
        self.assertEqual(test_headers, ['Service', 'Status', 'Revision', 'Port', 'Git', 'Worker'])

    def test__append_ports_in_field(self):
        self.box.data['port_view'] = PortView.name
        test_name = self.box._append_ports_in_field('name')
        test_status = self.box._append_ports_in_field('status')
        self.assertEqual(test_name, u"django (↘ 8081)")
        self.assertEqual(test_status, "Running")

        self.box.data['port_view'] = PortView.status
        test_name = self.box._append_ports_in_field('name')
        test_status = self.box._append_ports_in_field('status')
        self.assertEqual(test_name, "django")
        self.assertEqual(test_status, u"Running (↘ 8081)")


    def test_run(self):
        test_result = "data"
        self.box.run()
        self.assertEqual(self.box.widget, test_result)

    def test__get_service_category_data(self):
        self.fail()

    def test_format_revision(self):
        self.fail()


class TestUpdate_box(TestCase):
    def test_update_box(self):
        self.fail()
