from cabrita.components.box import Box
from cabrita.components.config import Config, Compose
from cabrita.components.dashboard import Dashboard
from cabrita.components.docker import DockerInspect, PortDirection
from cabrita.components.git import GitInspect
from cabrita.components.watchers import DockerComposeWatch, SystemWatch, UserWatch


class DashboardCommand:
    compose: Compose
    config: Config

    def __int__(self, path: str) -> None:
        self.cabrita_path = path

    def add_config(self) -> None:
        self.config = Config()
        self.config.add_path(self.cabrita_path)
        self.config.load_data()

    def add_compose(self) -> None:
        self.compose = Compose()
        for compose in self.config.compose_files:
            self.compose.add_path(compose)
        self.compose.load_data()

    def _add_watchers(self) -> None:
        self.dashboard.compose_watch = DockerComposeWatch()
        self.dashboard.system_watch = SystemWatch()
        self.dashboard.user_watches = UserWatch()
        for watch in self.config.watchers:
            self.dashboard.user_watches.add_watch(watch)

    def _add_boxes(self):
        for box_data in self.config.boxes:
            docker = DockerInspect(
                ports=box_data.get('show_ports', PortDirection.hidden),
                files_to_watch=box_data.get('files_to_watch', []),
                services_to_check_git=box_data.get('services_to_check_git', []),
            )
            git = GitInspect(
                target_branch=box_data.get('target_branch', ""),
                interval=box_data.get('git_fetch_interval', 30),
                compose=self.compose
            )
            box = Box(
                compose=self.compose,
                docker=docker,
                git=git
            )
            self.dashboard.add_box(box)

    def execute(self):
        self.dashboard = Dashboard(self.config.layout)
        self._add_watchers()
        self._add_boxes()
