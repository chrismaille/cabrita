from typing import Union
from unittest import TestCase, mock

from cabrita.command import CabritaCommand


def return_git_result(*args, **kwargs) -> Union[str, bool]:
    command = args[0]
    if 'describe' in command:
        return '2.0.1'
    if 'rev-parse' in command:
        return '457ac8c'
    if 'branch' in command:
        return '* master'
    if 'status' in command:
        return \
            """
            ## 2.0...origin/2.0 [behind 1]
             M cabrita/tests/test_dockerInspect.py
             M cabrita/tests/test_gitInspect.py
             M requirements.txt
            """
    else:
        return False


class TestGitInspect(TestCase):

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
        self.git = command.dashboard.all_boxes[-1].git

    @mock.patch('cabrita.abc.utils.run_command', side_effect=return_git_result)
    def test_get_git_revision_from_path(self, *mocks):
        self.git.run = mocks[0]
        test_string = self.git.get_git_revision_from_path(path='/', show_branch=True)
        self.assertEqual(test_string, u'✎ 2.0.1 ⑂ master@457ac8c')

    @mock.patch('cabrita.abc.utils.run_command', side_effect=return_git_result)
    def test_get_git_revision(self, *mocks):
        self.git.run = mocks[0]
        test_revision = self.git.get_git_revision('django')
        self.assertEqual(test_revision, u'✎ 2.0.1 ⑂ 457ac8c')

    @mock.patch('os.path.isdir', return_value=True)
    @mock.patch('cabrita.abc.utils.run_command', side_effect=return_git_result)
    def test_get_behind_state(self, *mocks):
        self.git.run = mocks[0]
        test_behind = self.git.get_behind_state('/')
        self.assertEqual(test_behind, 'OK')

    def test_inspect(self):
        self.fail()

    def test__get_modifications_in_target_branch(self):
        self.fail()

    def test__get_modifications_in_branch(self):
        self.fail()

    def test__get_active_branch(self):
        self.fail()

    def test__get_abbreviate_name(self):
        self.fail()

    def test__get_commits(self):
        self.fail()

    def test__get_commits_from_target(self):
        self.fail()
