#!/usr/bin/env python3
"""mdiffer — Identifies duplicate movie folders between two directories."""

import os
import re
import sys

LOG_DIR = './log'
OUTPUT_DIR = './output'
TRAILING_YEAR_RE = re.compile(r'\s+\(\d{4}\)$')


def setup():
    """Create the output and log directories if they do not already exist.

    :raises SystemExit: If the directories cannot be created due to a
        permissions error or other OS-level failure.
    """
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(LOG_DIR, exist_ok=True)
        print('Setup complete.')
    except OSError as e:
        print('Error during setup: {}'.format(e))
        sys.exit(1)


def get_dir_listing(directory):
    """Return a list of entry names in the given directory.

    :param directory: Absolute or relative path to the directory to list.
    :type directory: str
    :returns: List of file and folder names inside *directory*.
    :rtype: list
    :raises SystemExit: If *directory* does not exist or cannot be read.
    """
    if not os.path.isdir(directory):
        print('Error: "{}" is not a valid directory.'.format(directory))
        sys.exit(1)
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


def find_duplicates(secondary, primary):
    """Find names that appear in both the secondary and primary lists.

    Uses a set for O(n) average-case lookup instead of O(n^2) nested loops,
    which is significantly faster for large movie libraries.

    :param secondary: Cleaned names from the secondary movie directory.
    :type secondary: list
    :param primary: Cleaned names from the primary movie directory.
    :type primary: list
    :returns: List of names present in both *secondary* and *primary*.
    :rtype: list
    """
    primary_set = set(primary)
    return [name for name in secondary if name in primary_set]


def write_results(duplicates):
    """Write the list of duplicate names to ``output/dupes.txt``.

    :param duplicates: List of duplicate movie folder names to write.
    :type duplicates: list
    """
    output_path = os.path.join(OUTPUT_DIR, 'dupes.txt')
    with open(output_path, 'w') as f:
        for name in duplicates:
            f.write('{}\n'.format(name))


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
    setup()

    primary_dir = get_dir('primary movie directory')
    secondary_dir = get_dir('secondary movie directory')

    print('Reading directories...')
    primary_names = get_dir_listing(primary_dir)
    secondary_names = get_dir_listing(secondary_dir)

    print('Cleaning names...')
    log_path = os.path.join(LOG_DIR, 'log.txt')
    with open(log_path, 'w') as log:
        clean_primary = clean_names(primary_names, log)
        clean_secondary = clean_names(secondary_names, log)

    print('Finding duplicates...')
    duplicates = find_duplicates(clean_secondary, clean_primary)

    print('Writing results...')
    write_results(duplicates)

    print('\nDone! Total duplicates found: {}\n'.format(len(duplicates)))
    for name in duplicates:
        print(name)


if __name__ == '__main__':
    main()
