
import os
import psutil
import re
import subprocess
import sys
import yaml
from buzio import console, formatStr
from git import Repo
from cabrita import dashing
from time import sleep


class Dashboard():

    def __init__(self, docker_compose_path):
        self.path = docker_compose_path
        self.data = None
        self.services = None

    def get_compose_data(self):
        try:
            dcfile = os.path.join(self.path, "docker-compose.yml")
            with open(dcfile, 'r') as file:
                self.data = yaml.load(file.read())
            self.services = sorted(self.data['services'])
        except IOError as exc:
            console.error("Cannot open file: {}".format(exc))
            sys.exit(1)
        except yaml.YAMLError as exc:
            console.error("Cannot read file: {}".format(exc))
            sys.exit(1)
        except Exception as exc:
            console.error("Error: {}".format(exc))
            sys.exit(1)

    def get_services(self):
        return dashing.Text("SERVICES", color=1, border_color=5, title="Docker Apps")

    def get_infra(self):
        return dashing.Text("INFRA", color=1, border_color=5, title="Docker Infra")

    def get_info(self):
        cpu_percent = round(psutil.cpu_percent(interval=None) * 10, 0) / 10
        free_memory = int(psutil.virtual_memory().available / 1024 / 1024)
        total_memory = int(psutil.virtual_memory().total / 1024 / 1024)
        memory_percent = (free_memory / total_memory) * 100
        if memory_percent > 100:
            memory_percent = 100
        widget = dashing.HSplit(
            dashing.ColorRangeVGauge(
                val=memory_percent,
                colormap=((20, 1), (40, 3), (100, 2)),
                border_color=5,
                title="CPU: {}%".format(cpu_percent)
            ),
            dashing.ColorRangeVGauge(
                val=cpu_percent,
                colormap=((50, 2), (70, 3), (100, 1)),
                border_color=5,
                title="Free Mem: {}".format(free_memory)
            ),
            title="Host Info"
        )
        return widget

    def get_status(self):
        return dashing.Text("STATUS", color=1, border_color=5,)

    def run(self):
        self.get_compose_data()
        while True:
            services = self.get_services()
            infra = self.get_infra()
            status = self.get_status()
            info = self.get_info()
            ui = dashing.VSplit(
                dashing.HSplit(
                    services,
                    infra,
                    info
                ),
                status
            )
            ui.display()
            sleep(2)

#     def get_branch(self, name):
#         """Summary

#         Args:
#             name (TYPE): Description

#         Returns:
#             TYPE: Description
#         """
#         if COMPOSE_DATA['services'][name].get('build'):
#             data = COMPOSE_DATA['services'][name]['build']['context']
#             s = re.search(r"\w+", data)
#             if s:
#                 env = s.group(0)
#                 path = os.environ.get(env)
#                 self.repo = Repo(path)
#                 text = self.repo.active_branch.name
#             else:
#                 text = data
#         else:
#             text = "Using Image"
#         return text

#     def get_git_status(self):
#         """Summary

#         Returns:
#             TYPE: Description
#         """
#         text = "--"
#         if self.repo.is_dirty():
#             text = "Modified"
#         ret = run_command(
#             "cd {} && git status -bs --porcelain".format(self.repo.working_dir),
#             get_stdout=True
#         )
#         if "behind" in ret:
#             text = "Need to Pull"
#         elif "ahead" in ret:
#             text = "Need to Push"
#         return text

#     def check_server(self, name, service_type):
#         """Summary

#         Args:
#             name (TYPE): Description
#             service_type (TYPE): Description

#         Returns:
#             TYPE: Description
#         """
#         if service_type != "server":
#             full_name = "{}-{}".format(name, service_type)
#         else:
#             full_name = name
#         found = [
#             k
#             for k in COMPOSE_DATA['services']
#             if k == full_name
#         ]
#         if not found:
#             text = ""
#         else:
#             ret = run_command(
#                 'docker ps | grep "{0}$\|{0}_run"'.format(full_name),
#                 get_stdout=True
#             )
#             if ret:
#                 text = "Running"
#             else:
#                 text = "--"
#         return text

#     def run(self):
#         ret = self.get_compose_data()
#         if not ret:
#             return False


# def main():
#     services = dashing.VSplit(dashing.Text("Hello World"), title="services")
#     ui = dashing.HSplit(services, title="Status")
#     while True:
#         ui.display()
#         sleep(1)


# def run_command(
#         task,
#         get_stdout=False,
#         run_stdout=False):
#     """Summary

#     Args:
#         task (TYPE): Description
#         get_stdout (bool, optional): Description
#         run_stdout (bool, optional): Description

#     Returns:
#         TYPE: Description
#     """
#     try:
#         if run_stdout:
#             command = subprocess.check_output(task, shell=True)

#             if not command:
#                 return False

#             ret = subprocess.call(command, shell=True)

#         elif get_stdout is True:
#             ret = subprocess.check_output(task, shell=True)
#         else:
#             ret = subprocess.call(
#                 task,
#                 shell=True,
#                 stderr=subprocess.STDOUT
#             )

#         if ret != 0 and not get_stdout:
#             return False
#     except BaseException:
#         return False

#     return True if not get_stdout else ret.decode('utf-8')
