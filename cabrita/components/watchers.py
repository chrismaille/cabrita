# def get_check_status(self):
#     """Check Docker-Compose and Ngrok status.
#
#     Returns
#     -------
#         obj: gui.Text
#
#     """
#     # Check docker-compose.yml status
#     ret = run_command(
#         "cd {} && git fetch && git status -bs --porcelain".format(
#             self.path),
#         get_stdout=True
#     )
#     if not ret:
#         text = formatStr.warning(
#             "Can't find Docker-Compose status.\n",
#             use_prefix=False)
#     elif 'behind' in ret:
#         text = formatStr.error(
#             'Docker-Compose is OUTDATED.\n',
#             use_prefix=False)
#     else:
#         text = formatStr.success(
#             'Docker-Compose is up-to-date.\n',
#             use_prefix=False)
#     # Check Ngrok
#     if self.check_ngrok:
#         try:
#             ret = requests.get(
#                 "http://127.0.0.1:4040/api/tunnels", timeout=1)
#             if ret.status_code == 200:
#                 text += formatStr.success("Ngrok status: running",
#                                           use_prefix=False)
#             else:
#                 text += formatStr.error("Ngrok status: ERROR",
#                                         use_prefix=False)
#         except KeyboardInterrupt:
#             raise KeyboardInterrupt
#         except BaseException:
#             text += formatStr.error("Ngrok status: NOT RUNNING",
#                                     use_prefix=False)
#     return gui.Text(text, border_color=5, title="Check Status")
from typing import List

from cabrita.components.box import Box


class Watch(Box):

    def run(self):
        pass


class DockerComposeWatch(Watch):
    widget = "Docker-Compose Watcher"


class UserWatch(Watch):
    widget = "Hello World User Watchers"
    _watchers: List[str] = []

    def add_watch(self, watch: str) -> None:
        self._watchers.append(watch)


class SystemWatch(Watch):
    widget = "System Watcher"
