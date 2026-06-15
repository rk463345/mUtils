#!/usr/bin/env python3
"""mtui.py — Terminal UI front-end for the mUtils movie management toolkit.

Provides a full-screen, keyboard-driven menu.  Navigate with the arrow keys
or vim-style j/k, select with Enter, and press Q to quit.  Each tool shows
an input form and displays captured output in-window.

Usage::

    python3 mtui.py
"""

import curses
import sys

# Import logic functions (not main()) from each tool so the originals are
# never modified and can still be used standalone.
from . import mdiffer
from . import mremover
from . import mrenamer
from . import msymlinker

VERSION = '1.0'

# Pairs defined in _init_colors()
PAIR_TITLE    = 1   # yellow bold  — main title
PAIR_SELECTED = 2   # cyan bold    — highlighted menu item
PAIR_DIM      = 3   # default dim  — footer / descriptions
PAIR_BORDER   = 4   # cyan         — box border


# ── Terminal helpers ──────────────────────────────────────────────────────────

def _init_colors():
    """Initialise colour pairs; fall back gracefully if colours unavailable."""
    if not curses.has_colors():
        return
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(PAIR_TITLE,    curses.COLOR_YELLOW, -1)
    curses.init_pair(PAIR_SELECTED, curses.COLOR_CYAN,   -1)
    curses.init_pair(PAIR_DIM,      -1,                  -1)
    curses.init_pair(PAIR_BORDER,   curses.COLOR_CYAN,   -1)


def _clamp(text, width):
    """Truncate *text* to *width* characters to prevent curses overflow.

    :param text: String to truncate.
    :type text: str
    :param width: Maximum character width.
    :type width: int
    :returns: Possibly truncated string.
    :rtype: str
    """
    return text[:max(0, width)]


def _hline(win, y, width):
    """Draw a horizontal rule across the window at row *y*.

    :param win: curses window.
    :param y: Row index.
    :type y: int
    :param width: Total window width (inner characters drawn = width - 2).
    :type width: int
    """
    try:
        win.addch(y, 0, curses.ACS_LTEE)
        win.hline(y, 1, curses.ACS_HLINE, width - 2)
        win.addch(y, width - 1, curses.ACS_RTEE)
    except curses.error:
        pass


def _safe_addstr(win, y, x, text, attr=curses.A_NORMAL):
    """Wrapper around ``win.addstr`` that silently ignores out-of-bounds errors.

    :param win: curses window.
    :param y: Row.
    :type y: int
    :param x: Column.
    :type x: int
    :param text: String to draw.
    :type text: str
    :param attr: curses attribute flags.
    :type attr: int
    """
    try:
        win.addstr(y, x, text, attr)
    except curses.error:
        pass


# ── Input field ───────────────────────────────────────────────────────────────

def _input_field(win, y, x, label, max_width=52, prefill=''):
    """Display *label* then read a line of text from the user.

    Uses ``curses.echo`` so the user can see what they type.  Returns the
    entered string, or *prefill* if the user presses Enter on an empty field
    that already has a default value.

    :param win: curses window to draw in.
    :param y: Row for the field.
    :type y: int
    :param x: Starting column.
    :type x: int
    :param label: Prompt text displayed to the left of the input box.
    :type label: str
    :param max_width: Maximum number of characters accepted.
    :type max_width: int
    :param prefill: Default value shown inside the input box.
    :type prefill: str
    :returns: The user-entered (or pre-filled) string, stripped of whitespace.
    :rtype: str
    """
    height, width = win.getmaxyx()
    safe_width = min(max_width, width - x - len(label) - 6)

    _safe_addstr(win, y, x, label, curses.A_BOLD)
    field_x = x + len(label)

    # Draw the input box outline
    _safe_addstr(win, y, field_x, '[')
    _safe_addstr(win, y, field_x + 1, (prefill + ' ' * safe_width)[:safe_width])
    _safe_addstr(win, y, field_x + 1 + safe_width, ']')
    win.refresh()

    # Enable echo and position the cursor
    curses.echo()
    curses.curs_set(1)
    win.move(y, field_x + 1)
    win.refresh()

    try:
        raw = win.getstr(y, field_x + 1, safe_width)
        entered = raw.decode('utf-8', errors='replace').strip()
    except Exception:
        entered = ''
    finally:
        curses.noecho()
        curses.curs_set(0)

    return entered if entered else prefill


# ── Output display ────────────────────────────────────────────────────────────

def _show_output(win, text, start_y):
    """Render captured output below *start_y* inside *win*.

    :param win: curses window.
    :param text: Multi-line output string to display.
    :type text: str
    :param start_y: First row available for output content.
    :type start_y: int
    """
    height, width = win.getmaxyx()
    _hline(win, start_y, width)
    _safe_addstr(win, start_y, 2, ' Output ', curses.A_BOLD)

    lines = text.splitlines() if text else ['(no output)']
    available = height - start_y - 3
    display = lines[-available:] if len(lines) > available else lines

    for i, line in enumerate(display):
        row = start_y + 1 + i
        if row >= height - 2:
            break
        _safe_addstr(win, row, 2, _clamp(line, width - 4))


def _wait_for_key(win, height, width):
    """Show a 'press any key' prompt and wait for input.

    :param win: curses window.
    :param height: Window height.
    :type height: int
    :param width: Window width.
    :type width: int
    """
    _safe_addstr(win, height - 2, 2,
                 _clamp('Press any key to return to menu…', width - 4),
                 curses.A_DIM)
    win.refresh()
    win.getch()


# ── Tool runner ───────────────────────────────────────────────────────────────

def _run_tool(fn):
    """Execute *fn* and return displayable output as a string.

    :param fn: Zero-argument callable containing the tool logic.
    :type fn: callable
    :returns: Text returned by *fn*, or an error message.
    :rtype: str
    """
    try:
        result = fn()
    except SystemExit:
        return ''
    except Exception as exc:
        return 'Error: {}\n'.format(exc)
    return '' if result is None else str(result)


def _run_mremover_task(src, ext, dry_run, exclude_raw=''):
    """Run mremover with TUI-provided values and return displayable text."""
    result = mremover.remover(
        src,
        ext,
        dry_run=dry_run,
        exclude_paths=mremover.parse_exclude_paths(exclude_raw)
    )
    return mremover.format_remove_result(result)


# ── Tool screens ──────────────────────────────────────────────────────────────

def _screen_header(win, title, subtitle):
    """Draw standard screen chrome: border, title, subtitle, divider.

    :param win: curses window (should be the full screen).
    :param title: Bold title text.
    :type title: str
    :param subtitle: Dimmer subtitle / description text.
    :type subtitle: str
    """
    height, width = win.getmaxyx()
    win.clear()
    win.box()
    _safe_addstr(win, 1, 2, _clamp(title, width - 4),
                 curses.color_pair(PAIR_SELECTED) | curses.A_BOLD)
    _safe_addstr(win, 2, 2, _clamp(subtitle, width - 4), curses.A_DIM)
    _hline(win, 3, width)
    _safe_addstr(win, 4, 2,
                 _clamp('Fill in the fields below, then press Enter on each one.'
                        '  Leave blank + Enter to cancel.', width - 4),
                 curses.A_DIM)


def screen_mdiffer(win):
    """Interactive screen for the mdiffer tool.

    :param win: Full-screen curses window.
    """
    height, width = win.getmaxyx()
    _screen_header(win, 'mdiffer — Find Duplicate Movies',
                   'Compare two directories and list movies present in both.')
    win.refresh()

    primary = _input_field(win, 6, 2, 'Primary Directory:   ')
    if not primary:
        return
    secondary = _input_field(win, 8, 2, 'Secondary Directory: ')
    if not secondary:
        return

    _safe_addstr(win, 10, 2, 'Running…  ', curses.A_BOLD)
    win.refresh()

    def task():
        result = mdiffer.run_diff(primary, secondary)
        return mdiffer.format_diff_result(result)

    output = _run_tool(task)

    # Clear the "Running…" message before drawing output
    _safe_addstr(win, 10, 2, ' ' * 12)
    _show_output(win, output, 11)
    _wait_for_key(win, height, width)


def screen_mremover(win):
    """Interactive screen for the mremover tool.

    :param win: Full-screen curses window.
    """
    height, width = win.getmaxyx()
    _screen_header(win, 'mremover — Remove Files by Extension',
                   'Delete all files with a given extension inside a directory.')
    win.refresh()

    src = _input_field(win, 6, 2, 'Source Directory:      ')
    if not src:
        return
    ext = _input_field(win, 8, 2, 'Extension (e.g. .nfo): ', prefill='.nfo')
    if not ext:
        return

    exclude_raw = _input_field(win, 10, 2, 'Exclude paths:       ')

    dry_raw = _input_field(win, 12, 2, 'Dry run? [Y/n]:       ', prefill='Y')
    dry_run = dry_raw.strip().lower() not in ('n', 'no')

    if not dry_run:
        confirm = _input_field(win, 14, 2, 'Type DELETE:         ')
        if confirm != 'DELETE':
            return

    run_y = 16 if not dry_run else 14
    _safe_addstr(win, run_y, 2, 'Running…  ', curses.A_BOLD)
    win.refresh()

    output = _run_tool(
        lambda: _run_mremover_task(src, ext, dry_run, exclude_raw)
    )

    _safe_addstr(win, run_y, 2, ' ' * 12)
    _show_output(win, output, run_y + 1)
    _wait_for_key(win, height, width)


def screen_mrenamer(win):
    """Interactive screen for the mrenamer tool.

    :param win: Full-screen curses window.
    """
    height, width = win.getmaxyx()
    _screen_header(win, 'mrenamer — Rename Movie Folders',
                   'Rename scene-style folders/files to "Title (Year)" format.')
    win.refresh()

    src = _input_field(win, 6, 2, 'Source Directory: ')
    if not src:
        return

    _safe_addstr(win, 8, 2, 'Running…  ', curses.A_BOLD)
    win.refresh()

    output = _run_tool(
        lambda: mrenamer.format_rename_result(mrenamer.renamer(src))
    )

    _safe_addstr(win, 8, 2, ' ' * 12)
    _show_output(win, output, 9)
    _wait_for_key(win, height, width)


def screen_msymlinker(win):
    """Interactive screen for the msymlinker tool.

    :param win: Full-screen curses window.
    """
    height, width = win.getmaxyx()
    _screen_header(win, 'msymlinker — Create Symlink',
                   'Create a soft symlink from a new location to the original.')
    win.refresh()

    src = _input_field(win, 6, 2, 'Source Directory:      ')
    if not src:
        return
    old_name = _input_field(win, 8, 2, 'Original Folder Name:  ')
    if not old_name:
        return
    dest = _input_field(win, 10, 2, 'Destination Directory: ')
    if not dest:
        return
    new_name = _input_field(win, 12, 2, 'Symlink Name:          ')
    if not new_name:
        return

    _safe_addstr(win, 14, 2, 'Running…  ', curses.A_BOLD)
    win.refresh()

    output = _run_tool(
        lambda: msymlinker.format_link_result(
            msymlinker.linker(src, old_name, dest, new_name)
        )
    )

    _safe_addstr(win, 14, 2, ' ' * 12)
    _show_output(win, output, 15)
    _wait_for_key(win, height, width)


# ── Menu definition ───────────────────────────────────────────────────────────

MENU = [
    ('mdiffer',     'Find duplicate movies between two directories', screen_mdiffer),
    ('mremover',    'Remove files by extension from a directory',    screen_mremover),
    ('mrenamer',    'Rename movie folders and files to clean format', screen_mrenamer),
    ('msymlinker',  'Create a soft symlink from new location to original', screen_msymlinker),
    ('Quit',        'Exit mUtils', None),
]

_LONGEST_NAME = max(len(name) for name, _, _ in MENU)


# ── Main menu ─────────────────────────────────────────────────────────────────

def main_menu(stdscr):
    """Draw and run the interactive main menu loop.

    :param stdscr: Root curses window provided by ``curses.wrapper``.
    """
    _init_colors()
    curses.curs_set(0)
    selected = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        stdscr.box()

        # ── Title block ───────────────────────────────────────────────────────
        title = 'mUtils v{}'.format(VERSION)
        sub   = 'Movie Management Tools'
        _safe_addstr(stdscr, 1,
                     max(2, (width - len(title)) // 2),
                     _clamp(title, width - 4),
                     curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
        _safe_addstr(stdscr, 2,
                     max(2, (width - len(sub)) // 2),
                     _clamp(sub, width - 4),
                     curses.A_DIM)
        _hline(stdscr, 3, width)

        # ── Menu items ────────────────────────────────────────────────────────
        desc_x = 4 + 3 + _LONGEST_NAME + 4   # prefix + name + spacing

        for i, (name, desc, _) in enumerate(MENU):
            y = 5 + i * 2
            if y >= height - 4:
                break
            is_sel = (i == selected)

            prefix = u'\u25b6  ' if is_sel else '   '    # ▶  or spaces
            name_attr = (curses.color_pair(PAIR_SELECTED) | curses.A_BOLD
                         if is_sel else curses.A_NORMAL)
            desc_attr = (curses.color_pair(PAIR_SELECTED)
                         if is_sel else curses.A_DIM)

            _safe_addstr(stdscr, y, 4, _clamp(prefix + name, width - 6), name_attr)
            if desc_x < width - 10:
                _safe_addstr(stdscr, y, desc_x,
                             _clamp(u'\u2014 ' + desc, width - desc_x - 2),
                             desc_attr)

        # ── Footer ────────────────────────────────────────────────────────────
        _hline(stdscr, height - 3, width)
        footer = (u'\u2191\u2193  Navigate    '
                  u'1\u20134  Jump to tool    '
                  u'Enter  Select    '
                  u'Q  Quit')
        _safe_addstr(stdscr, height - 2, 2,
                     _clamp(footer, width - 4),
                     curses.A_DIM)

        stdscr.refresh()

        # ── Input handling ────────────────────────────────────────────────────
        key = stdscr.getch()

        if key in (curses.KEY_UP, ord('k')):
            selected = (selected - 1) % len(MENU)

        elif key in (curses.KEY_DOWN, ord('j')):
            selected = (selected + 1) % len(MENU)

        elif key in (curses.KEY_ENTER, ord('\n'), ord('\r')):
            _, _, fn = MENU[selected]
            if fn is None:        # Quit
                break
            fn(stdscr)

        elif ord('1') <= key <= ord('4'):
            idx = key - ord('1')
            if idx < len(MENU) - 1:
                _, _, fn = MENU[idx]
                fn(stdscr)

        elif key in (ord('q'), ord('Q')):
            break


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    """Launch the mUtils terminal interface."""
    try:
        curses.wrapper(main_menu)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
