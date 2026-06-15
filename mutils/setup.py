"""Environment setup and diagnostics for mUtils."""

import argparse
import importlib
import json
import os
import sys
import tempfile
from dataclasses import asdict, dataclass

from . import mdiffer


@dataclass(frozen=True)
class SetupCheck:
    """One setup or environment check result."""

    name: str
    ok: bool
    required: bool
    message: str


@dataclass(frozen=True)
class SetupResult:
    """Structured setup command result."""

    checks: list
    output_dir: str
    log_dir: str
    check_only: bool

    @property
    def success(self):
        """Return ``True`` when every required check passed."""
        return all(check.ok or not check.required for check in self.checks)


def _check_python_version():
    """Check the active Python version."""
    required = (3, 10)
    current = sys.version_info[:3]
    ok = current >= required
    return SetupCheck(
        'python',
        ok,
        True,
        'Python {}.{}.{}{}'.format(
            current[0],
            current[1],
            current[2],
            ' is supported' if ok else ' is below 3.10'
        )
    )


def _check_imports(module_names):
    """Check that required package modules can be imported."""
    checks = []
    for module_name in module_names:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            checks.append(SetupCheck(
                'import {}'.format(module_name),
                False,
                True,
                str(exc)
            ))
        else:
            checks.append(SetupCheck(
                'import {}'.format(module_name),
                True,
                True,
                'imported'
            ))
    return checks


def _check_optional_import(module_name, label):
    """Check an optional UI dependency."""
    try:
        importlib.import_module(module_name)
    except Exception as exc:
        return SetupCheck(label, False, False, str(exc))
    return SetupCheck(label, True, False, 'available')


def _check_dirs(output_dir, log_dir, check_only=False):
    """Create and verify runtime directories."""
    checks = []
    for label, directory in [('output directory', output_dir), ('log directory', log_dir)]:
        try:
            if not check_only:
                os.makedirs(directory, exist_ok=True)

            if not os.path.isdir(directory):
                checks.append(SetupCheck(
                    label,
                    False,
                    True,
                    'does not exist: {}'.format(directory)
                ))
                continue

            test_path = os.path.join(directory, '.mutils-write-test')
            with open(test_path, 'w') as test_file:
                test_file.write('ok')
            os.remove(test_path)
        except OSError as exc:
            checks.append(SetupCheck(label, False, True, str(exc)))
        else:
            checks.append(SetupCheck(label, True, True, 'writable: {}'.format(directory)))
    return checks


def _check_symlink_capability():
    """Check whether the current environment can create symlinks."""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            original = os.path.join(temp_dir, 'original')
            link = os.path.join(temp_dir, 'link')
            os.mkdir(original)
            os.symlink(original, link)
            if not os.path.islink(link):
                return SetupCheck('symlink capability', False, False,
                                  'created path is not a symlink')
    except (OSError, NotImplementedError) as exc:
        return SetupCheck('symlink capability', False, False, str(exc))

    return SetupCheck('symlink capability', True, False, 'available')


def run_setup(output_dir=mdiffer.OUTPUT_DIR, log_dir=mdiffer.LOG_DIR,
              check_only=False):
    """Run setup checks and optionally create runtime directories."""
    checks = [
        _check_python_version(),
        *_check_imports([
            'mutils.mdiffer',
            'mutils.mremover',
            'mutils.mrenamer',
            'mutils.msymlinker',
        ]),
        *_check_dirs(output_dir, log_dir, check_only=check_only),
        _check_optional_import('tkinter', 'tkinter GUI support'),
        _check_optional_import('curses', 'curses TUI support'),
        _check_symlink_capability(),
    ]
    return SetupResult(checks, output_dir, log_dir, check_only)


def format_setup_result(result):
    """Return human-readable output for setup results."""
    lines = [
        'mUtils setup {}'.format('check' if result.check_only else 'run'),
        'Output directory: {}'.format(result.output_dir),
        'Log directory: {}'.format(result.log_dir),
        '',
    ]
    for check in result.checks:
        status = 'OK' if check.ok else ('WARN' if not check.required else 'FAIL')
        lines.append('[{}] {} - {}'.format(status, check.name, check.message))

    lines.append('')
    lines.append('Required checks {}'.format(
        'passed.' if result.success else 'failed.'
    ))
    return '\n'.join(lines)


def result_to_json(result):
    """Serialize setup results for scripts."""
    return json.dumps({
        'success': result.success,
        'output_dir': result.output_dir,
        'log_dir': result.log_dir,
        'check_only': result.check_only,
        'checks': [asdict(check) for check in result.checks],
    }, indent=2)


def _build_parser():
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        description='Create runtime directories and check mUtils environment support.'
    )
    parser.add_argument(
        '--output-dir',
        default=mdiffer.OUTPUT_DIR,
        help='directory for mdiffer output files'
    )
    parser.add_argument(
        '--log-dir',
        default=mdiffer.LOG_DIR,
        help='directory for mdiffer log files'
    )
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='check environment without creating runtime directories'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='emit machine-readable JSON'
    )
    return parser


def main(argv=None):
    """Entry point for the mutils-setup command."""
    args = _build_parser().parse_args(argv)
    result = run_setup(
        output_dir=args.output_dir,
        log_dir=args.log_dir,
        check_only=args.check_only
    )
    print(result_to_json(result) if args.json else format_setup_result(result))
    sys.exit(0 if result.success else 1)
