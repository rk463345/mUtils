#!/usr/bin/env python3
"""mremover — Removes files matching a given extension from a directory tree."""

import os
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class RemoveResult:
    """Structured result for a removal run."""

    success: bool
    matched_paths: list
    removed_paths: list
    dry_run: bool
    error: str = ''

    def __bool__(self):
        return self.success


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

    Walks *src* recursively, including files directly inside *src*.  Optionally
    runs in dry-run mode, which reports matches without deleting anything.

    :param src: The root directory whose subdirectories will be searched.
    :type src: str
    :param extension: The file extension to target for removal (e.g. ``'.nfo'``).
    :type extension: str
    :param dry_run: When ``True``, print matching files but do not delete them.
    :type dry_run: bool
    :returns: Structured result describing matched and removed files.
    :rtype: RemoveResult
    """
    if not os.path.isdir(src):
        return RemoveResult(False, [], [], dry_run,
                            '"{}" is not a valid directory.'.format(src))

    extension = _normalize_extension(extension)
    if extension is None:
        return RemoveResult(False, [], [], dry_run,
                            'extension must not be empty.')

    matched_paths = []
    removed_paths = []
    try:
        for root, _, files in os.walk(src):
            for item in files:
                if item.endswith(extension):
                    target = os.path.join(root, item)
                    matched_paths.append(target)
                    if not dry_run:
                        os.remove(target)
                        removed_paths.append(target)
        return RemoveResult(True, matched_paths, removed_paths, dry_run)

    except (OSError, PermissionError) as e:
        return RemoveResult(False, matched_paths, removed_paths, dry_run, str(e))


def format_remove_result(result):
    """Return human-readable output for a :class:`RemoveResult`."""
    if not result.success:
        return 'Error: {}'.format(result.error)

    action = 'Would remove' if result.dry_run else 'Removed'
    paths = result.matched_paths if result.dry_run else result.removed_paths
    lines = ['{} file(s): {}'.format(action, len(paths))]
    for path in paths:
        prefix = '[dry-run] Would remove' if result.dry_run else 'Removed'
        lines.append('{}: {}'.format(prefix, path))
    return '\n'.join(lines)


def main():
    """Entry point for mremover."""
    source = input('Source Directory: ')
    ext = input('Extension type to be removed (e.g. .nfo): ')

    preview = input('Preview files before deleting? [y/n]: ').strip().lower()
    if preview == 'y':
        print('\n--- Dry run ---')
        print(format_remove_result(remover(source, ext, dry_run=True)))
        confirm = input('\nProceed with deletion? [y/n]: ').strip().lower()
        if confirm != 'y':
            print('Aborted.')
            sys.exit(0)

    result = remover(source, ext)
    print(format_remove_result(result))
    if result:
        print('Complete.')
    else:
        print('Something went wrong.')


if __name__ == '__main__':
    main()
