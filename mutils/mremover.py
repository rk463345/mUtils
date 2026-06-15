#!/usr/bin/env python3
"""mremover — Removes files matching a given extension from a directory tree."""

import argparse
import csv
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


def parse_exclude_paths(raw):
    """Parse CSV-style exclusion paths from user input."""
    if not raw:
        return []
    return [path.strip() for path in next(csv.reader([raw])) if path.strip()]


def _path_key(path):
    """Return an absolute normalized path key."""
    return os.path.normcase(os.path.abspath(path))


def _is_excluded(path, exclude_keys):
    """Return ``True`` when *path* is inside an excluded path."""
    path_key = _path_key(path)
    for exclude_key in exclude_keys:
        try:
            if os.path.commonpath([path_key, exclude_key]) == exclude_key:
                return True
        except ValueError:
            continue
    return False


def remover(src, extension, dry_run=False, exclude_paths=None,
            case_sensitive=False):
    """Remove all files ending with *extension* inside *src*.

    Walks *src* recursively, including files directly inside *src*.  Optionally
    runs in dry-run mode, which reports matches without deleting anything.

    :param src: The root directory whose subdirectories will be searched.
    :type src: str
    :param extension: The file extension to target for removal (e.g. ``'.nfo'``).
    :type extension: str
    :param dry_run: When ``True``, print matching files but do not delete them.
    :type dry_run: bool
    :param exclude_paths: Optional paths to skip while walking *src*.
    :type exclude_paths: list or None
    :param case_sensitive: When ``True``, require exact extension casing.
    :type case_sensitive: bool
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

    exclude_keys = [_path_key(path) for path in (exclude_paths or [])]
    extension_key = extension if case_sensitive else extension.casefold()

    matched_paths = []
    removed_paths = []
    try:
        for root, dirs, files in os.walk(src):
            dirs[:] = [
                directory for directory in dirs
                if not _is_excluded(os.path.join(root, directory), exclude_keys)
            ]
            if _is_excluded(root, exclude_keys):
                continue
            for item in files:
                target = os.path.join(root, item)
                if _is_excluded(target, exclude_keys):
                    continue

                item_key = item if case_sensitive else item.casefold()
                if item_key.endswith(extension_key):
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


def _build_parser():
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        description='Remove files by extension from a directory tree.'
    )
    parser.add_argument('source', nargs='?', help='source directory to scan')
    parser.add_argument('extension', nargs='?', help='extension to remove')
    parser.add_argument(
        '--exclude',
        action='append',
        default=[],
        metavar='PATH',
        help='path to exclude; may be repeated and may contain commas'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='show matching files without deleting them'
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help='confirm deletion when running non-interactively'
    )
    parser.add_argument(
        '--case-sensitive',
        action='store_true',
        help='require exact extension casing'
    )
    return parser


def main(argv=None):
    """Entry point for mremover."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    cli_mode = args.source is not None or args.extension is not None
    if cli_mode and (args.source is None or args.extension is None):
        parser.error('source and extension are required together')

    if cli_mode:
        if not args.dry_run and not args.yes:
            parser.error('deletion requires --yes or --dry-run')
        result = remover(
            args.source,
            args.extension,
            dry_run=args.dry_run,
            exclude_paths=args.exclude,
            case_sensitive=args.case_sensitive
        )
        print(format_remove_result(result))
        sys.exit(0 if result else 1)

    source = input('Source Directory: ')
    ext = input('Extension type to be removed (e.g. .nfo): ')
    exclude_raw = input('Paths to exclude, CSV quoted if needed (optional): ')
    exclude_paths = parse_exclude_paths(exclude_raw)

    preview = input('Preview files before deleting? [y/n]: ').strip().lower()
    if preview == 'y':
        print('\n--- Dry run ---')
        print(format_remove_result(
            remover(source, ext, dry_run=True, exclude_paths=exclude_paths)
        ))
        confirm = input('\nProceed with deletion? [y/n]: ').strip().lower()
        if confirm != 'y':
            print('Aborted.')
            sys.exit(0)
    else:
        confirm = input('Delete without preview? Type DELETE to continue: ').strip()
        if confirm != 'DELETE':
            print('Aborted.')
            sys.exit(0)

    result = remover(source, ext, exclude_paths=exclude_paths)
    print(format_remove_result(result))
    if result:
        print('Complete.')
    else:
        print('Something went wrong.')


if __name__ == '__main__':
    main()
