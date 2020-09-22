"""
PC-BASIC - video_cli.py
Command-line interface

(c) 2013--2020 Rob Hagemans
This file is released under the GNU GPL version 3 or later.
"""

import sys
import time

from .video import VideoPlugin
from .base import video_plugins, InitFailed
from ..basic.base import signals
from ..basic.base import scancode
from ..basic.base.eascii import as_unicode as uea
from ..compat import EOF, console


# escape sequence to scancode
KEY_TO_SCAN = {
    'F1': scancode.F1,  'F2': scancode.F2,  'F3': scancode.F3,  'F4': scancode.F4,
    'F5': scancode.F5,  'F6': scancode.F6,  'F7': scancode.F7,  'F8': scancode.F8,
    'F9': scancode.F9,  'F10': scancode.F10,  'F11': scancode.F11, 'F12': scancode.F12,
    'END': scancode.END,  'HOME': scancode.HOME,
    'UP': scancode.UP,  'DOWN': scancode.DOWN,  'RIGHT': scancode.RIGHT,  'LEFT': scancode.LEFT,
    'INSERT': scancode.INSERT,  'DELETE': scancode.DELETE,  'PAGEUP': scancode.PAGEUP,
    'PAGEDOWN': scancode.PAGEDOWN,
}
MOD_TO_SCAN = {
    'SHIFT': scancode.LSHIFT,
    'CTRL': scancode.CTRL,
    'ALT': scancode.ALT,
}
# escape sequence to e-ASCII
KEY_TO_EASCII = {
    'F1': uea.F1,  'F2': uea.F2,  'F3': uea.F3,  'F4': uea.F4,  'F5': uea.F5,
    'F6': uea.F6,  'F7': uea.F7,  'F8': uea.F8,  'F9': uea.F9,  'F10': uea.F10,
    'F11': uea.F11,  'F12': uea.F12,  'END': uea.END,
    'HOME': uea.HOME,  'UP': uea.UP,  'DOWN': uea.DOWN,
    'RIGHT': uea.RIGHT,  'LEFT': uea.LEFT,  'INSERT': uea.INSERT,
    'DELETE': uea.DELETE,  'PAGEUP': uea.PAGEUP,  'PAGEDOWN': uea.PAGEDOWN,
}

SHIFT_KEY_TO_EASCII = {
    'F1': uea.SHIFT_F1,
    'F2': uea.SHIFT_F2,
    'F3': uea.SHIFT_F3,
    'F4': uea.SHIFT_F4,
    'F5': uea.SHIFT_F5,
    'F6': uea.SHIFT_F6,
    'F7': uea.SHIFT_F7,
    'F8': uea.SHIFT_F8,
    'F9': uea.SHIFT_F9,
    'F10': uea.SHIFT_F10,
    'F11': uea.SHIFT_F11,
    'F12': uea.SHIFT_F12,
    'HOME': uea.SHIFT_HOME,
    'UP': uea.SHIFT_UP,
    'PAGEUP': uea.SHIFT_PAGEUP,
    'LEFT': uea.SHIFT_LEFT,
    'RIGHT': uea.SHIFT_RIGHT,
    'END': uea.SHIFT_END,
    'DOWN': uea.SHIFT_DOWN,
    'PAGEDOWN': uea.SHIFT_PAGEDOWN,
    'INSERT': uea.SHIFT_INSERT,
    'DELETE': uea.SHIFT_DELETE,
}

CTRL_KEY_TO_EASCII = {
    'F1': uea.CTRL_F1,
    'F2': uea.CTRL_F2,
    'F3': uea.CTRL_F3,
    'F4': uea.CTRL_F4,
    'F5': uea.CTRL_F5,
    'F6': uea.CTRL_F6,
    'F7': uea.CTRL_F7,
    'F8': uea.CTRL_F8,
    'F9': uea.CTRL_F9,
    'F10': uea.CTRL_F10,
    'F11': uea.CTRL_F11,
    'F12': uea.CTRL_F12,
    'HOME': uea.CTRL_HOME,
    'PAGEUP': uea.CTRL_PAGEUP,
    'LEFT': uea.CTRL_LEFT,
    'RIGHT': uea.CTRL_RIGHT,
    'END': uea.CTRL_END,
    'PAGEDOWN': uea.CTRL_PAGEDOWN,
    #'ESCAPE': uea.CTRL_ESCAPE,
    #'BACKSPACE': uea.CTRL_BACKSPACE,
    #'2': uea.CTRL_2,
    #'6': uea.CTRL_6,
    #'MINUS': uea.CTRL_MINUS,
}

ALT_KEY_TO_EASCII = {
    '1': uea.ALT_1,
    '2': uea.ALT_2,
    '3': uea.ALT_3,
    '4': uea.ALT_4,
    '5': uea.ALT_5,
    '6': uea.ALT_6,
    '7': uea.ALT_7,
    '8': uea.ALT_8,
    '9': uea.ALT_9,
    '0': uea.ALT_0,
    '-': uea.ALT_MINUS,
    '=': uea.ALT_EQUALS,
    'q': uea.ALT_q,
    'w': uea.ALT_w,
    'e': uea.ALT_e,
    'r': uea.ALT_r,
    't': uea.ALT_t,
    'y': uea.ALT_y,
    'u': uea.ALT_u,
    'i': uea.ALT_i,
    'o': uea.ALT_o,
    'p': uea.ALT_p,
    'a': uea.ALT_a,
    's': uea.ALT_s,
    'd': uea.ALT_d,
    'f': uea.ALT_f,
    'g': uea.ALT_g,
    'h': uea.ALT_h,
    'j': uea.ALT_j,
    'k': uea.ALT_k,
    'l': uea.ALT_l,
    'z': uea.ALT_z,
    'x': uea.ALT_x,
    'c': uea.ALT_c,
    'v': uea.ALT_v,
    'b': uea.ALT_b,
    'n': uea.ALT_n,
    'm': uea.ALT_m,
    '\b': uea.ALT_BACKSPACE,
    '\t': uea.ALT_TAB,
    '\r': uea.ALT_RETURN,
    ' ': uea.ALT_SPACE,
    'F1': uea.ALT_F1,
    'F2': uea.ALT_F2,
    'F3': uea.ALT_F3,
    'F4': uea.ALT_F4,
    'F5': uea.ALT_F5,
    'F6': uea.ALT_F6,
    'F7': uea.ALT_F7,
    'F8': uea.ALT_F8,
    'F9': uea.ALT_F9,
    'F10': uea.ALT_F10,
    'F11': uea.ALT_F11,
    'F12': uea.ALT_F12,
}


class VideoTextBase(VideoPlugin):
    """Text-based interface."""

    def __init__(self, input_queue, video_queue, **kwargs):
        """Initialise text-based interface."""
        if not console:
            raise InitFailed('This interface requires a console terminal (tty).')
        VideoPlugin.__init__(self, input_queue, video_queue)
        # start the stdin thread for non-blocking reads
        self._input_handler = InputHandlerCLI(input_queue)

    def _check_input(self):
        """Handle keyboard events."""
        self._input_handler.drain_queue()


@video_plugins.register('cli')
class VideoCLI(VideoTextBase):
    """Command-line interface."""

    def __init__(self, input_queue, video_queue, **kwargs):
        """Initialise command-line interface."""
        VideoTextBase.__init__(self, input_queue, video_queue)
        # current row and column where the cursor should be
        # keep cursor_row and last_row unset at the start to avoid printing extra line on resume
        # as it will see a move frm whatever we set it at here to the actusl cursor row
        self._cursor_row, self._cursor_col = None, 1
        # current actual print column
        self._col = 1
        # cursor row on last cycle
        self._last_row = None
        # text buffer
        self._text = [[u' '] * 80 for _ in range(25)]


    def __enter__(self):
        """Open command-line interface."""
        VideoTextBase.__enter__(self)
        console.set_raw()

    def __exit__(self, type, value, traceback):
        """Close command-line interface."""
        try:
            if self._col != 1:
                console.write(u'\r\n')
            console.unset_raw()
        finally:
            VideoTextBase.__exit__(self, type, value, traceback)

    def _work(self):
        """Display update cycle."""
        # update cursor row only if it's changed from last work-cycle
        # or if actual printing takes place on the new cursor row
        if self._cursor_row != self._last_row or self._cursor_col != self._col:
            self._update_position(self._cursor_row, self._cursor_col)

    ###############################################################################

    def update(self, row, col, unicode_matrix, attr_matrix, y0, x0, sprite):
        """Put text or pixels at a given position."""
        for unicode_list in unicode_matrix:
            unicode_list = [(_c if _c != u'\0' else u' ') for _c in unicode_list]
            self._text[row-1][col-1:col-1+len(unicode_list)] = unicode_list
            # show the character only if it's on the cursor row
            if row == self._cursor_row:
                # may have to update row!
                if row != self._last_row or col != self._col:
                    self._update_position(row, col)
                console.write(u''.join((_c if _c else u' ') for _c in unicode_list))
                self._col = col + len(unicode_list)
            row += 1
            # the terminal cursor has moved, so we'll need to move it back later
            # if that's not where we want to be
            # but often it is anyway

    def move_cursor(self, row, col, attr, width):
        """Move the cursor to a new position."""
        # update cursor row only if it's changed from last work-cycle
        # or if actual printing takes place on the new cursor row
        self._cursor_row, self._cursor_col = row, col

    def clear_rows(self, back_attr, start, stop):
        """Clear screen rows."""
        self._text[start-1:stop] = [[u' '] * len(self._text[0]) for _ in range(start-1, stop)]
        if start <= self._cursor_row and stop >= self._cursor_row:
            self._update_position(self._cursor_row, 1)
            self._redraw_row(self._cursor_row)

    def scroll(self, direction, from_line, scroll_height, back_attr):
        """Scroll the screen between from_line and scroll_height."""
        if direction == -1:
            self._scroll_up(from_line, scroll_height, back_attr)
        else:
            self._scroll_down(from_line, scroll_height, back_attr)

    def _scroll_up(self, from_line, scroll_height, back_attr):
        """Scroll the screen up between from_line and scroll_height."""
        self._text[from_line-1:scroll_height] = (
            self._text[from_line:scroll_height] + [[u' '] * len(self._text[0])]
        )
        console.write(u'\r\n')

    def _scroll_down(self, from_line, scroll_height, back_attr):
        """Scroll the screen down between from_line and scroll_height."""
        self._text[from_line-1:scroll_height] = (
            [[u' '] * len(self._text[0])] + self._text[from_line-1:scroll_height-1]
        )

    def set_mode(self, canvas_height, canvas_width, text_height, text_width):
        """Initialise video mode """
        self._text = [[u' '] * text_width for _ in range(text_height)]

    def _redraw_row(self, row, until=None):
        """Draw the stored text in a row."""
        if not row:
            return
        console.write('\r')
        rowtext = (u''.join(self._text[row-1])).replace(u'\0', u' ')
        if until:
            rowtext = rowtext[:(until-1)]
        console.write(rowtext)
        self._col = len(self._text[row-1])+1

    def _update_position(self, row, col):
        """Move terminal print location."""
        # move cursor if necessary
        if row and row != self._last_row:
            if self._last_row:
                console.write(u'\r\n')
                self._col = 1
            self._last_row = row
            # show what's on the line where we are.
            self._redraw_row(row)
            # redraw until current column to put cursor in the right position
            if col:
                self._redraw_row(row, until=col)
        elif row and col and col != self._col:
            # we're on the current row
            # only redraw if column has changed
            self._redraw_row(row, until=col)
            self._col = col


###############################################################################

class InputHandlerCLI(object):
    """Keyboard reader thread."""

    def __init__(self, queue):
        """Start the keyboard reader."""
        self._input_queue = queue
        self._f12_active = False
        self.quit_on_eof = True

    def drain_queue(self):
        """Handle keyboard events."""
        while True:
            # s is one unicode char or one scancode
            uc, sc, mods = self._get_key()
            if not uc and not sc:
                break
            if uc == EOF and self.quit_on_eof:
                # ctrl-D (unix) / ctrl-Z (windows)
                self._input_queue.put(signals.Event(signals.QUIT))
            elif uc == u'\x7f':
                # backspace
                self._input_queue.put(
                    signals.Event(signals.KEYB_DOWN, (uea.BACKSPACE, scancode.BACKSPACE, []))
                )
            elif sc or uc:
                # check_full=False to allow pasting chunks of text
                self._input_queue.put(signals.Event(signals.KEYB_DOWN, (uc, sc, mods)))
                # this is needed since we don't send key-up events at all otherwise
                if sc == scancode.F12:
                    self._f12_active = True
                elif self._f12_active:
                    self._input_queue.put(signals.Event(signals.KEYB_UP, (scancode.F12,)))
                    self._f12_active = False

    def _get_key(self):
        """Retrieve one keypress."""
        char, key, mods = console.read_key()
        if not char and not key:
            return None, None, []
        # override characters wth alt
        if 'ALT' in mods and 'CTRL' not in mods:
            char = ALT_KEY_TO_EASCII.get(key, u'')
        # don't override ctrl characters
        if not char:
            if 'CTRL' in mods and 'ALT' not in mods:
                char = CTRL_KEY_TO_EASCII.get(key, u'')
            elif mods == {'SHIFT'}:
                char = SHIFT_KEY_TO_EASCII.get(key, char)
            else:
                char = KEY_TO_EASCII.get(key, char)
        scan = KEY_TO_SCAN.get(key, None)
        modscan = [MOD_TO_SCAN[mod] for mod in mods if mod in MOD_TO_SCAN]
        return char, scan, modscan
