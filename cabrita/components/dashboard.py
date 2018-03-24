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
        self.boxes = []
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
                        ui = self.get_layout(term)
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
        self.boxes.append(box)

    def get_layout(self, term):
        main_box = [
            box.widget
            for box in self.boxes
            if box.main
        ][0]
        small_boxes = [
            box.widget
            for box in self.boxes
            if box.size == "small" and not box.main
        ]
        large_boxes = [
            box.widget
            for box in self.boxes
            if box.size == "large" and not box.main
        ]

        if main_box.size == "small":
            small_boxes.insert(0, main_box.widget)
        else:
            large_boxes.insert(0, main_box.widget)


        st = dashing.VSplit(
            self.box_check.widget,
            dashing.VSplit(
                self.box_warnings.widget,
                self.box_stats.widget
            )
        )
        sm = dashing.HSplit(*small_boxes, st) if small_boxes else st

        if self.layout == "horizontal":
            func = dashing.HSplit
        else:
            func = dashing.VSplit
        if large_boxes:
            ui = func(*large_boxes, sm, terminal=term, main=True)
        else:
            ui = func(sm, terminal=term, main=True)

        return ui
