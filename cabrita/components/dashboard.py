import os
import sys

from blessed import Terminal
from buzio import console
from dashing import dashing
from dashing.dashing import HSplit, VSplit
from raven import Client
from typing import Union

from cabrita.components.box import Box
from cabrita.components.config import Config

client = None
if os.getenv('CABRITA_SENTRY_DSN'):
    client = Client(os.getenv('CABRITA_SENTRY_DSN'))


class Dashboard:
    """
    Main dashboard class.

    Initiate the main loop.
    """
    def __init__(self, config: Config) -> None:
        self.small_boxes = []
        self.large_boxes = []
        self.compose_watch: Box = None
        self.user_watches: Box = None
        self.system_watch: Box = None
        self.config = config
        self.layout = self.config.layout

    def _log_box(self, box):
        log_text = f"Box '{box.title}' added."
        if box.docker.interval > 0:
            log_text += f" Inspecting docker containers each {box.docker.interval} seconds."
        if box.git.interval > 0:
            log_text += f" Inspecting git repositories each {box.git.interval} seconds."
        if box.interval > 0:
            log_text += f' Refreshing data each {box.interval} seconds.'
        log_text += f" Services inside: {', '.join(box.services)}."
        console.info(log_text)

    def run(self) -> None:
        term = Terminal()
        try:
            with term.fullscreen():
                with term.hidden_cursor():
                    while True:
                        ui = self._get_layout(term)
                        ui.display()
        except KeyboardInterrupt:
            print(term.color(0))
            sys.exit(0)
        except BaseException as exc:
            if client:
                client.captureException()
            raise exc

    def add_box(self, box: Box) -> None:
        box_list = self.small_boxes if box.size == 'small' else self.large_boxes
        box_list.insert(
            0 if box.main else len(box_list),
            box
        )
        self._log_box(box)

    def _get_layout(self, term) -> Union[HSplit, VSplit]:

        st = VSplit(
            self.user_watches.widget,
            VSplit(
                self.compose_watch.widget,
                self.system_watch.widget,
                background_color=self.config.background_color_value
            ),
            background_color=self.config.background_color_value
        )
        small_box_widgets = [
            b.widget
            for b in self.small_boxes
        ]
        sm = dashing.HSplit(*small_box_widgets, st, background_color=self.config.background_color_value) if small_box_widgets else st

        if self.layout == "horizontal":
            func = HSplit
        else:
            func = VSplit

        large_box_widgets = [
            b.widget
            for b in self.large_boxes
        ]
        if large_box_widgets:
            ui = func(*large_box_widgets, sm, terminal=term, main=True, background_color=self.config.background_color_value)
        else:
            ui = func(sm, terminal=term, main=True, background_color=self.config.background_color_value)

        return ui
