import importlib

import pytest


def test_gui_task_runner_returns_text():
    pytest.importorskip('tkinter')
    mgui = importlib.import_module('mgui')

    assert mgui._run_task(lambda: 'done') == 'done'
    assert mgui._run_task(lambda: None) == ''


def test_gui_task_runner_formats_errors():
    pytest.importorskip('tkinter')
    mgui = importlib.import_module('mgui')

    def broken():
        raise ValueError('bad input')

    assert mgui._run_task(broken) == 'Error: bad input\n'


def test_tui_task_runner_returns_text():
    pytest.importorskip('curses')
    mtui = importlib.import_module('mtui')

    assert mtui._run_tool(lambda: 'done') == 'done'
    assert mtui._run_tool(lambda: None) == ''


def test_tui_task_runner_formats_errors():
    pytest.importorskip('curses')
    mtui = importlib.import_module('mtui')

    def broken():
        raise ValueError('bad input')

    assert mtui._run_tool(broken) == 'Error: bad input\n'
