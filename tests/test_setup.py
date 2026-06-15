import json

import pytest

from mutils import setup


def _required_checks(result):
    return [check for check in result.checks if check.required]


def test_run_setup_creates_runtime_directories(tmp_path):
    output_dir = tmp_path / 'output'
    log_dir = tmp_path / 'log'

    result = setup.run_setup(str(output_dir), str(log_dir))

    assert result.success is True
    assert output_dir.is_dir()
    assert log_dir.is_dir()
    assert all(check.ok for check in _required_checks(result))


def test_run_setup_check_only_does_not_create_directories(tmp_path):
    output_dir = tmp_path / 'output'
    log_dir = tmp_path / 'log'

    result = setup.run_setup(str(output_dir), str(log_dir), check_only=True)

    assert result.success is False
    assert not output_dir.exists()
    assert not log_dir.exists()


def test_setup_json_output_contains_checks(tmp_path):
    result = setup.run_setup(str(tmp_path / 'output'), str(tmp_path / 'log'))
    payload = json.loads(setup.result_to_json(result))

    assert payload['success'] is True
    assert payload['output_dir'] == str(tmp_path / 'output')
    assert payload['log_dir'] == str(tmp_path / 'log')
    assert any(check['name'] == 'python' for check in payload['checks'])


def test_format_setup_result_marks_optional_failures_as_warnings():
    result = setup.SetupResult(
        checks=[
            setup.SetupCheck('required', True, True, 'ok'),
            setup.SetupCheck('optional', False, False, 'missing'),
        ],
        output_dir='output',
        log_dir='log',
        check_only=True,
    )

    formatted = setup.format_setup_result(result)

    assert '[OK] required - ok' in formatted
    assert '[WARN] optional - missing' in formatted
    assert 'Required checks passed.' in formatted


def test_setup_main_exits_successfully_for_json(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        setup.main([
            '--output-dir',
            str(tmp_path / 'output'),
            '--log-dir',
            str(tmp_path / 'log'),
            '--json',
        ])

    assert exc.value.code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload['success'] is True
