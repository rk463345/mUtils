import importlib

import pytest


def test_gui_module_imports_without_constructing_tk():
    mgui = importlib.import_module('mgui')

    assert hasattr(mgui, '_run_task')


def test_gui_task_runner_returns_text():
    mgui = importlib.import_module('mgui')

    assert mgui._run_task(lambda: 'done') == 'done'
    assert mgui._run_task(lambda: None) == ''


def test_gui_task_runner_formats_errors():
    mgui = importlib.import_module('mgui')

    def broken():
        raise ValueError('bad input')

    assert mgui._run_task(broken) == 'Error: bad input\n'


def test_gui_mremover_task_passes_exclusions(monkeypatch):
    mgui = importlib.import_module('mgui')
    calls = {}

    def fake_remover(src, ext, dry_run=False, exclude_paths=None):
        calls.update({
            'src': src,
            'ext': ext,
            'dry_run': dry_run,
            'exclude_paths': exclude_paths,
        })
        return 'result'

    monkeypatch.setattr(mgui.mremover, 'remover', fake_remover)
    monkeypatch.setattr(mgui.mremover, 'format_remove_result', str)

    assert mgui._run_mremover_task('src', '.nfo', True, 'a, b') == 'result'
    assert calls == {
        'src': 'src',
        'ext': '.nfo',
        'dry_run': True,
        'exclude_paths': ['a', 'b'],
    }


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


def test_tui_mremover_task_passes_exclusions(monkeypatch):
    pytest.importorskip('curses')
    mtui = importlib.import_module('mtui')
    calls = {}

    def fake_remover(src, ext, dry_run=False, exclude_paths=None):
        calls.update({
            'src': src,
            'ext': ext,
            'dry_run': dry_run,
            'exclude_paths': exclude_paths,
        })
        return 'result'

    monkeypatch.setattr(mtui.mremover, 'remover', fake_remover)
    monkeypatch.setattr(mtui.mremover, 'format_remove_result', str)

    assert mtui._run_mremover_task('src', '.nfo', False, 'a, b') == 'result'
    assert calls == {
        'src': 'src',
        'ext': '.nfo',
        'dry_run': False,
        'exclude_paths': ['a', 'b'],
    }
