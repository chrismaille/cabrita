from cabrita.components.box import Box
from cabrita.components.config import Config, Compose
from cabrita.components.dashboard import Dashboard
from cabrita.components.docker import DockerInspect, PortDirection
from cabrita.components.git import GitInspect
from cabrita.components.watchers import DockerComposeWatch, SystemWatch, UserWatch


class DashboardCommand:
    compose: Compose
    config: Config

    def add_config(self, path: str) -> None:
        self.cabrita_path = path
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

    def _add_services_in_boxes(self):
        included_services = []
        main_box = None
        for name in self.config.boxes:
            box_data = self.config.boxes[name]
            docker = DockerInspect(
                ports=box_data.get('show_ports', PortDirection.hidden),
                files_to_watch=box_data.get('watch_build_files', []),
                services_to_check_git=box_data.get('watch_git_services', []),
                compose=self.compose,
                interval=box_data.get('interval', 0)
            )
            git = GitInspect(
                target_branch=box_data.get('target_branch', ""),
                interval=box_data.get('git_fetch_interval', 30),
                compose=self.compose
            )

            services_in_box = []
            for service in self.compose.services:
                if service not in included_services and service not in self.config.ignore_services:
                    for name in box_data.get('includes', []):
                        if name.lower() in service.lower():
                            services_in_box.append(service)
                            included_services.append(service)

            box = Box()
            box.compose = self.compose
            box.docker = docker
            box.git = git
            box.services = services_in_box
            box.load_data(box_data)

            if box.main:
                main_box = box
            else:
                self.dashboard.add_box(box)
        for service in self.compose.services:
            if service not in included_services and service not in self.config.ignore_services:
                main_box.add_service(service)
        self.dashboard.add_box(main_box)

    def execute(self):
        self.dashboard = Dashboard(self.config.layout)
        self._add_watchers()
        self._add_services_in_boxes()
        self.dashboard.run()
