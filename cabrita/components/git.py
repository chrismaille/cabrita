import os
import re
from enum import Enum
from typing import Tuple

from buzio import formatStr

from cabrita.abc.base import InspectTemplate

ARROW_UP = u"↑"
ARROW_DOWN = u"↓"


class GitDirection(Enum):
    ahead = 1
    behind = 2


class GitInspect(InspectTemplate):

    def __init__(self, compose, interval: int, target_branch: str) -> None:

        super(GitInspect, self).__init__(compose, interval)
        self.target_branch = target_branch
        self.modified = False
        self.default_data = ""


    def get_git_revision_from_path(self, path):
        git_tag = self.run(
            'cd {} && git describe --tags $(git rev-list --tags --max-count=1 2>/dev/null) 2>/dev/null'.format(path),
            get_stdout=True
        )
        git_hash = self.run(
            'cd {} && git rev-parse --short HEAD 2>/dev/null'.format(path),
            get_stdout=True
        )
        if not git_hash and git_tag:
            git_status = "--"
        else:
            git_status = u"✎ {}@⑂ {}".format(
                git_tag.replace('\n', '')[:10],
                git_hash.replace('\n', '')
            ) if git_tag else u"⑂ {}".format(git_hash.replace('\n', ''))
        return git_status


    def get_git_revision(self, service):
        if self.compose.is_image(service):
            return "-"
        path = self.compose.get_build_path(service)
        return self.get_git_revision_from_path(path)


    def get_behind_state(self, path):

        if not os.path.isdir(os.path.join(path, '.git')):
            return "OK"

        git_behind = self.run(
            "cd {} && git fetch && git status -bs --porcelain 2> /dev/null".format(path),
            get_stdout=True
        )

        if not git_behind:
            git_state = ""
        elif 'behind' in git_behind:
            git_state = formatStr.error('NEED PULL', use_prefix=False)
        else:
            git_state = formatStr.success("OK", use_prefix=False)
        return git_state


    def inspect(self, service: str) -> str:
        self.modified = False
        if self.compose.is_image(service):
            return formatStr.info("Using Image", use_prefix=False)

        self.path = self.compose.get_build_path(service)
        branch = self._get_active_branch()

        if branch:
            branch_is_dirty = self.run(
                "cd {} && git status --porcelain 2>/dev/null".format(self.path),
                get_stdout=True
            )
            self.modified = True if branch_is_dirty else False

            branch_ahead, branch_behind = self._get_modifications_in_branch()
            target_branch_ahead, target_branch_behind = self._get_modifications_in_target_branch(branch)

            text = "{}{}{}".format(
                self._get_abbreviate_name(branch),
                formatStr.error(" {} {}".format(ARROW_DOWN, branch_behind), use_prefix=False) if branch_behind else "",
                formatStr.error(" {} {}".format(ARROW_UP, branch_ahead), use_prefix=False) if branch_ahead else ""
            )
            if target_branch_ahead or target_branch_behind:
                text += " ({}{}{})".format(
                    self.target_branch,
                    formatStr.error(" {} {}".format(ARROW_DOWN, target_branch_behind),
                                    use_prefix=False) if target_branch_behind else "",
                    formatStr.error(" {} {}".format(ARROW_UP, target_branch_ahead),
                                    use_prefix=False) if target_branch_ahead else ""
                )
            self._status[service] = formatStr.warning(text, use_prefix=False) if self.modified else formatStr.success(text,
                                                                                                             use_prefix=False)
        else:
            self._status[service] = formatStr.error(
                "Branch Not Found",
                use_prefix=False
            )

    def _get_modifications_in_target_branch(self, branch: str) -> Tuple[int, int]:
        if self.target_branch and \
                branch != self.target_branch.replace("origin/", ""):
            target_branch_ahead = self._get_commits_from_target(self.path, branch, GitDirection.ahead)
            target_branch_behind = self._get_commits_from_target(self.path, branch, GitDirection.behind)
            return target_branch_ahead, target_branch_behind
        else:
            return 0, 0

    def _get_modifications_in_branch(self) -> Tuple[int, int]:
        branch_ahead = self._get_commits(self.path, GitDirection.ahead)
        branch_behind = self._get_commits(self.path, GitDirection.behind)
        return branch_ahead, branch_behind

    def _get_active_branch(self) -> str:
        branch = self.run(
            "cd {} && git branch | grep \"*\" 2>/dev/null".format(self.path),
            get_stdout=True
        )
        return branch.replace("* ", "").replace("\n", "") if branch else ""


    def _get_abbreviate_name(self, full_name) -> str:
        name = full_name.split("/")[-1]
        if len(name) > 15:
            return "{}...".format(name[:12])
        else:
            return name

    def _get_commits(self, path, direction: GitDirection) -> int:

        task = "cd {} && git status -bs --porcelain".format(path)
        ret = self.run(task, get_stdout=True)
        if direction == GitDirection.behind:
            if "behind" in ret:
                s = re.search(r"behind (\d+)", ret)
                return int(s.group(1))
            else:
                return 0
        elif "ahead" in ret:
            s = re.search(r"ahead (\d+)", ret)
            return int(s.group(1))
        else:
            return 0

    def _get_commits_from_target(self, path: str, name: str, direction: GitDirection) -> int:

        task = "cd {} && git log {}..{} --oneline 2>/dev/null".format(
            path,
            name if direction == GitDirection.behind else self.target_branch,
            self.target_branch if direction == GitDirection.behind else name
        )
        ret = self.run(task, get_stdout=True)
        return 0 if not ret else len(ret.split("\n")) - 1
