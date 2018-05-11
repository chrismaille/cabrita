import signal
import sys
from datetime import datetime
from multiprocessing.pool import Pool
from multiprocessing import TimeoutError
from typing import Union

from blessed import Terminal
from buzio import console, formatStr
from colorama import Style
from dashing import dashing
from dashing.dashing import HSplit, VSplit

from cabrita.components.box import Box, update_box
from cabrita.components.config import Config


class Dashboard:
    """
    Main dashboard class.

    Initiate the main loop.
    """

    def __init__(self, config: Config) -> None:
        self.small_boxes = []
        self.large_boxes = []
        self.compose_watch = None
        self.user_watches = None
        self.system_watch = None
        self.config = config
        self.layout = self.config.layout
        self.background_color = config.background_color_value

    @property
    def all_boxes(self) -> list:
        return [self.user_watches, self.compose_watch, self.system_watch] + self.large_boxes + self.small_boxes

    def _log_box(self, box: Box) -> None:
        log_text = "Box '{}' added.".format(box.title)
        if box.docker.interval > 1:
            log_text += " Inspecting docker containers each {} seconds.".format(box.docker.interval)
        if box.git.interval > 1:
            log_text += " Inspecting git repositories each {} seconds.".format(box.git.interval)
        if box.interval > 1:
            log_text += ' Refreshing data each {} seconds.'.format(box.interval)
        log_text += " Services: {}.".format(', '.join(box.services))
        console.info(log_text)

    def run(self) -> None:
        term = Terminal()
        try:
            with term.fullscreen():
                with term.hidden_cursor():
                    with term.cbreak():
                        while True:
                            key_pressed = term.inkey(timeout=0)
                            if 'q' in key_pressed.lower():
                                raise KeyboardInterrupt
                            ui = self._get_layout(term)
                            ui.display()
                            self._update_boxes()
        except KeyboardInterrupt:
            print(term.color(0))
            sys.exit(0)
        except BaseException as exc:
            print(term.exit_fullscreen)
            print(Style.RESET_ALL)
            raise exc

    def add_box(self, box: Box) -> None:
        box_list = self.small_boxes if box.size == 'small' else self.large_boxes
        box_list.insert(
            0 if box.main else len(box_list),
            box
        )
        self._log_box(box)

    def _update_boxes(self):
        boxes_needing_update = [
            self.user_watches,
            self.compose_watch,
            self.system_watch
        ]
        boxes_needing_update += [
            box
            for box in self.small_boxes + self.large_boxes
            if box.can_update
        ]
        original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
        pool = Pool()
        signal.signal(signal.SIGINT, original_sigint_handler)
        try:
            new_results = [pool.apply_async(update_box, [b]) for b in boxes_needing_update]
            new_widgets = [res.get(30) for res in new_results]

            self.user_watches.widget = new_widgets[0]
            self.compose_watch.widget = new_widgets[1]
            self.system_watch.widget = new_widgets[2]

            for index, box in enumerate(boxes_needing_update):
                if index < 3:
                    continue
                widget = new_widgets[index]
                box.widget = widget
                box.last_update = datetime.now()
            pool.terminate()
        except KeyboardInterrupt:
            pool.terminate()
            raise
        except TimeoutError:
            print(formatStr.error("TIMEOUT DURING REFRESHING DATA..."), file=sys.stderr)


    def _get_layout(self, term) -> Union[HSplit, VSplit]:

        st = VSplit(
            self.user_watches.widget,
            VSplit(
                self.compose_watch.widget,
                self.system_watch.widget
            )
        )
        small_box_widgets = [
            b.widget
            for b in self.small_boxes
        ]
        sm = dashing.HSplit(*small_box_widgets, st) if small_box_widgets else st

        if self.layout == "horizontal":
            func = HSplit
        else:
            func = VSplit

        large_box_widgets = [
            b.widget
            for b in self.large_boxes
        ]
        if large_box_widgets:
            ui = func(*large_box_widgets, sm, terminal=term, main=True, color=7,
                      background_color=self.background_color)
        else:
            ui = func(sm, terminal=term, main=True, color=7, background_color=self.background_color)

        return ui
