#!/usr/bin/env python3
"""mdiffer — Identifies duplicate movie folders between two directories."""

import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, 'log')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'output')
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


def setup(output_dir=OUTPUT_DIR, log_dir=LOG_DIR):
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
    return [
        primary_by_key[_match_key(name, case_sensitive)]
        for name in secondary
        if _match_key(name, case_sensitive) in primary_by_key
    ]


def _available_path(directory, stem, extension):
    """Return a non-existing path inside *directory*."""
    path = os.path.join(directory, stem + extension)
    if not os.path.exists(path):
        return path

    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
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
    setup(output_dir, log_dir)

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


def main():
    """Entry point for mdiffer."""
    primary_dir = get_dir('primary movie directory')
    secondary_dir = get_dir('secondary movie directory')

    try:
        result = run_diff(primary_dir, secondary_dir)
    except MUtilsError as exc:
        print('Error: {}'.format(exc))
        sys.exit(1)

    print(format_diff_result(result))


if __name__ == '__main__':
    main()
