#!/usr/bin/env python3
"""mdiffer — Identifies duplicate movie folders between two directories."""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(PACKAGE_DIR)
LOG_DIR = os.path.join(PROJECT_DIR, 'log')
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'output')
TRAILING_YEAR_RE = re.compile(r'\s+\(\d{4}\)$')


class MUtilsError(ValueError):
    """Raised when a tool cannot complete because of invalid input or I/O."""


@dataclass(frozen=True)
class DiffResult:
    """Structured result for a duplicate scan."""

    primary_dir: str
    secondary_dir: str
    duplicates: list
    output_path: str
    log_path: str


def ensure_output_dirs(output_dir=OUTPUT_DIR, log_dir=LOG_DIR):
    """Create the output and log directories if they do not already exist.

    :raises MUtilsError: If the directories cannot be created due to a
        permissions error or other OS-level failure.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)
    except OSError as e:
        raise MUtilsError('error during setup: {}'.format(e))


def get_dir_listing(directory):
    """Return a list of entry names in the given directory.

    :param directory: Absolute or relative path to the directory to list.
    :type directory: str
    :returns: List of file and folder names inside *directory*.
    :rtype: list
    :raises MUtilsError: If *directory* does not exist or cannot be read.
    """
    if not os.path.isdir(directory):
        raise MUtilsError('"{}" is not a valid directory.'.format(directory))
    return os.listdir(directory)


def clean_names(names, log=None):
    """Strip a trailing release year from a list of folder names.

    Expects names formatted as ``Movie Title (YYYY)``.  Only a final
    four-digit year in parentheses is removed; other parenthetical text is
    left unchanged.
    Cleaned mappings are optionally written to an open log file handle.

    :param names: Raw list of folder or file names to clean.
    :type names: list
    :param log: An open, writable file object for logging changes.
        Pass ``None`` to disable logging.
    :type log: file or None
    :returns: List of cleaned names with years removed where applicable.
    :rtype: list
    """
    cleaned = []
    for name in names:
        stripped = TRAILING_YEAR_RE.sub('', name)
        if stripped != name:
            if log is not None:
                log.write('Removing date from {} -> {}\n'.format(name, stripped))
        cleaned.append(stripped)
    return cleaned


def _match_key(name, case_sensitive=False):
    """Return a comparison key for duplicate matching."""
    return name if case_sensitive else name.casefold()


def find_duplicates(secondary, primary, case_sensitive=False):
    """Find names that appear in both the secondary and primary lists.

    Uses a set for O(n) average-case lookup instead of O(n^2) nested loops,
    which is significantly faster for large movie libraries.

    :param secondary: Cleaned names from the secondary movie directory.
    :type secondary: list
    :param primary: Cleaned names from the primary movie directory.
    :type primary: list
    :param case_sensitive: When ``True``, require exact case-sensitive matches.
    :type case_sensitive: bool
    :returns: List of names present in both *secondary* and *primary*.
    :rtype: list
    """
    primary_by_key = {}
    for name in primary:
        primary_by_key.setdefault(_match_key(name, case_sensitive), name)

    duplicates = []
    seen = set()
    for name in secondary:
        key = _match_key(name, case_sensitive)
        if key in primary_by_key and key not in seen:
            duplicates.append(primary_by_key[key])
            seen.add(key)
    return duplicates


def _available_path(directory, stem, extension):
    """Return a non-existing path inside *directory*."""
    path = os.path.join(directory, stem + extension)
    if not os.path.exists(path):
        return path

    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    path = os.path.join(directory, '{}-{}{}'.format(stem, timestamp, extension))
    if not os.path.exists(path):
        return path

    counter = 2
    while True:
        path = os.path.join(directory, '{}-{}-{}{}'.format(
            stem,
            timestamp,
            counter,
            extension
        ))
        if not os.path.exists(path):
            return path
        counter += 1


def write_results(duplicates, output_dir=OUTPUT_DIR, overwrite=False):
    """Write the list of duplicate names to ``output/dupes.txt``.

    :param duplicates: List of duplicate movie folder names to write.
    :type duplicates: list
    :param output_dir: Directory where ``dupes.txt`` should be written.
    :type output_dir: str
    :param overwrite: When ``True``, replace any existing ``dupes.txt``.
    :type overwrite: bool
    :returns: The path to the written file.
    :rtype: str
    """
    output_path = (
        os.path.join(output_dir, 'dupes.txt')
        if overwrite else _available_path(output_dir, 'dupes', '.txt')
    )
    with open(output_path, 'w') as f:
        for name in duplicates:
            f.write('{}\n'.format(name))
    return output_path


def run_diff(primary_dir, secondary_dir, output_dir=OUTPUT_DIR, log_dir=LOG_DIR,
             case_sensitive=False, overwrite=False):
    """Run the duplicate scan and return a structured result."""
    ensure_output_dirs(output_dir, log_dir)

    primary_names = get_dir_listing(primary_dir)
    secondary_names = get_dir_listing(secondary_dir)

    log_path = (
        os.path.join(log_dir, 'log.txt')
        if overwrite else _available_path(log_dir, 'log', '.txt')
    )
    with open(log_path, 'w') as log:
        clean_primary = clean_names(primary_names, log)
        clean_secondary = clean_names(secondary_names, log)

    duplicates = find_duplicates(
        clean_secondary,
        clean_primary,
        case_sensitive=case_sensitive
    )
    output_path = write_results(
        duplicates,
        output_dir=output_dir,
        overwrite=overwrite
    )

    return DiffResult(
        primary_dir=primary_dir,
        secondary_dir=secondary_dir,
        duplicates=duplicates,
        output_path=output_path,
        log_path=log_path,
    )


def format_diff_result(result):
    """Return human-readable output for a :class:`DiffResult`."""
    lines = [
        'Total duplicates found: {}'.format(len(result.duplicates)),
        'Results written to: {}'.format(result.output_path),
        'Log written to: {}'.format(result.log_path),
    ]
    if result.duplicates:
        lines.append('')
        lines.extend(result.duplicates)
    return '\n'.join(lines)


def get_dir(prompt):
    """Prompt the user to enter a directory path.

    :param prompt: Human-readable label describing the directory being requested.
    :type prompt: str
    :returns: The path string entered by the user.
    :rtype: str
    """
    return input('Input path for {}:\t'.format(prompt))


def _build_parser():
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        description='Find duplicate movie folders between two directories.'
    )
    parser.add_argument('primary_dir', nargs='?', help='primary movie directory')
    parser.add_argument('secondary_dir', nargs='?', help='secondary movie directory')
    parser.add_argument(
        '--output-dir',
        default=OUTPUT_DIR,
        help='directory for duplicate output files'
    )
    parser.add_argument(
        '--log-dir',
        default=LOG_DIR,
        help='directory for cleanup logs'
    )
    parser.add_argument(
        '--case-sensitive',
        action='store_true',
        help='require exact case-sensitive duplicate matches'
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='overwrite dupes.txt and log.txt instead of creating suffixed files'
    )
    return parser


def main(argv=None):
    """Entry point for mdiffer."""
    args = _build_parser().parse_args(argv)

    primary_dir = args.primary_dir or get_dir('primary movie directory')
    secondary_dir = args.secondary_dir or get_dir('secondary movie directory')

    try:
        result = run_diff(
            primary_dir,
            secondary_dir,
            output_dir=args.output_dir,
            log_dir=args.log_dir,
            case_sensitive=args.case_sensitive,
            overwrite=args.overwrite
        )
    except MUtilsError as exc:
        print('Error: {}'.format(exc))
        sys.exit(1)

    print(format_diff_result(result))


if __name__ == '__main__':
    main()
