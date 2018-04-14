import os

from cabrita.components.box import Box
from cabrita.components.config import Config, Compose
from cabrita.components.dashboard import Dashboard
from cabrita.components.docker import DockerInspect, PortView, PortDetail
from cabrita.components.git import GitInspect
from cabrita.components.watchers import DockerComposeWatch, SystemWatch, UserWatch


class DashboardCommand:

    def add_config(self, path: str, compose_path: tuple) -> None:
        self.cabrita_path = path
        self.config = Config()
        self.config.add_path(self.cabrita_path)
        self.config.load_data()
        self.config.manual_compose_paths = list(compose_path)

    def add_compose(self) -> None:
        self.compose = Compose()
        for compose in self.config.compose_files:
            self.compose.add_path(compose, base_path=os.path.dirname(compose))
        self.compose.load_data()
        if self.config.version == 0:
            self.config.generate_boxes(self.compose.services)

    def _add_watchers(self) -> None:
        git = GitInspect(
            target_branch="",
            interval=30,
            compose=self.compose
        )
        self.dashboard.compose_watch = DockerComposeWatch(
            background_color=self.config.background_color,
            git=git,
            config=self.config,
            version=self.version
        )
        self.dashboard.system_watch = SystemWatch(
            background_color=self.config.background_color
        )
        self.dashboard.user_watches = UserWatch(
            background_color=self.config.background_color,
            git=git,
            config=self.config
        )

    def _add_services_in_boxes(self):
        included_services = []
        main_box = None

        for name in self.config.boxes:
            box_data = self.config.boxes[name]
            docker = DockerInspect(compose=self.compose, interval=box_data.get('interval', 0),
                                   port_view=box_data.get('port_view', PortView.hidden),
                                   port_detail=box_data.get('port_detail', PortDetail.external),
                                   files_to_watch=box_data.get('watch_for_build_files', []),
                                   services_to_check_git=box_data.get('watch_for_build_git', []))
            git = GitInspect(
                target_branch=box_data.get('watch_branch', ""),
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

            box = Box(
                compose=self.compose,
                docker=docker,
                git=git,
                background_color=self.config.background_color
            )
            box.services = services_in_box
            box.load_data(box_data)

            if box.main:
                main_box = box
            else:
                self.dashboard.add_box(box)
        if main_box:
            for service in self.compose.services:
                if service not in included_services and service not in self.config.ignore_services:
                    main_box.add_service(service)
            self.dashboard.add_box(main_box)

    def execute(self):
        self.dashboard = Dashboard(config=self.config)
        self._add_watchers()
        self._add_services_in_boxes()
        self.dashboard.run()

    def add_version(self, version):
        self.version = version
