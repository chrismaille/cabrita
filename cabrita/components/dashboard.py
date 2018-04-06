import os
import sys
from raven import Client
from blessed import Terminal
from dashing import dashing
from buzio import console

client = None
if os.getenv('CABRITA_SENTRY_DSN'):
    client = Client(os.getenv('CABRITA_SENTRY_DSN'))


class Dashboard:
    def __init__(self, layout: str):
        self.small_boxes = []
        self.large_boxes = []
        self.box_check = None
        self.box_warnings = None
        self.box_stats = None
        self.layout = layout

    def run(self):
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
            console.error("Internal Error: {}".format(exc))
            if client:
                client.captureException()
            sys.exit(1)

    def add_box(self, box):
        box_list = self.small_boxes if box.size == 'small' else self.large_boxes
        box_list.insert(
            0 if box.main else len(box_list),
            box
        )

    def _get_layout(self, term):

        st = dashing.VSplit(
            self.box_check.widget,
            dashing.VSplit(
                self.box_warnings.widget,
                self.box_stats.widget
            )
        )
        small_box_widgets = [
            b.widget
            for b in self.small_boxes
        ]
        sm = dashing.HSplit(*small_box_widgets, st) if small_box_widgets else st

        if self.layout == "horizontal":
            func = dashing.HSplit
        else:
            func = dashing.VSplit

        large_box_widgets = [
            b.widget
            for b in self.large_boxes
        ]
        if large_box_widgets:
            ui = func(*large_box_widgets, sm, terminal=term, main=True)
        else:
            ui = func(sm, terminal=term, main=True)

        return ui
