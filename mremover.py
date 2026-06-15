#!/usr/bin/env python3
"""mremover — Removes files matching a given extension from a directory tree."""

import os
import sys


def _normalize_extension(extension):
    """Return a validated extension string, or ``None`` if invalid."""
    extension = extension.strip()
    if not extension:
        return None
    if not extension.startswith('.'):
        extension = '.' + extension
    return extension


def remover(src, extension, dry_run=False):
    """Remove all files ending with *extension* inside *src*.

    Walks one level deep — each immediate subdirectory of *src* is scanned
    for matching files.  Optionally runs in dry-run mode, which prints what
    would be deleted without actually deleting anything.

    :param src: The root directory whose subdirectories will be searched.
    :type src: str
    :param extension: The file extension to target for removal (e.g. ``'.nfo'``).
    :type extension: str
    :param dry_run: When ``True``, print matching files but do not delete them.
    :type dry_run: bool
    :returns: ``True`` if the operation completed without error, ``False`` otherwise.
    :rtype: bool
    """
    if not os.path.isdir(src):
        print('Error: "{}" is not a valid directory.'.format(src))
        return False

    extension = _normalize_extension(extension)
    if extension is None:
        print('Error: extension must not be empty.')
        return False

    try:
        dirs = os.listdir(src)
        for path in dirs:
            full_path = os.path.join(src, path)
            if not os.path.isdir(full_path):
                continue
            for item in os.listdir(full_path):
                if item.endswith(extension):
                    target = os.path.join(src, path, item)
                    if dry_run:
                        print('[dry-run] Would remove: {}'.format(target))
                    else:
                        print('Removing: {}'.format(target))
                        os.remove(target)
        return True

    except (OSError, PermissionError) as e:
        print('Error: {}'.format(e))
        return False


def main():
    """Entry point for mremover."""
    source = input('Source Directory: ')
    ext = input('Extension type to be removed (e.g. .nfo): ')

    preview = input('Preview files before deleting? [y/n]: ').strip().lower()
    if preview == 'y':
        print('\n--- Dry run ---')
        remover(source, ext, dry_run=True)
        confirm = input('\nProceed with deletion? [y/n]: ').strip().lower()
        if confirm != 'y':
            print('Aborted.')
            sys.exit(0)

    if remover(source, ext):
        print('Complete.')
    else:
        print('Something went wrong.')


if __name__ == '__main__':
    main()
