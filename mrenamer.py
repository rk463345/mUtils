#!/usr/bin/env python3
"""mrenamer — Renames movie folders and their contents to a clean format.

Converts dot-separated scene-style names such as::

    Movie.Name.2023.1080p.BluRay.x264-GROUP/
        Movie.Name.2023.1080p.BluRay.x264-GROUP.mkv

into human-readable names::

    Movie Name (2023)/
        Movie Name (2023).mkv
"""

import os
import re
import sys
from dataclasses import dataclass
from uuid import uuid4

#: Resolution and quality tags that mark the end of the movie title.
#: Everything from the first matching tag onward is discarded.
RESOLUTIONS = frozenset({'proper', '480p', '720p', '1080p', '2160p', '4k'})

#: Sub-folder and sample file names to skip during file renaming.
SKIP_NAMES = frozenset({'subs', 'sample'})

YEAR_RE = re.compile(r'^\d{4}$')


@dataclass(frozen=True)
class RenameOperation:
    """One planned filesystem rename."""

    src: str
    dst: str
    kind: str


class RenamePlanError(ValueError):
    """Raised when a rename plan cannot be applied safely."""


@dataclass(frozen=True)
class RenameResult:
    """Structured result for a rename run."""

    success: bool
    operations: list
    dry_run: bool
    error: str = ''

    def __bool__(self):
        return self.success


def _strip_encoding_tags(parts):
    """Remove resolution/encoding tags and all tokens that follow them.

    Iterates *parts* and stops collecting tokens as soon as one matches an
    entry in :data:`RESOLUTIONS` (case-insensitive).

    :param parts: Dot-split segments of a file or folder name, excluding
        the file extension and the year token.
    :type parts: list
    :returns: Trimmed list of title-word segments.
    :rtype: list
    """
    result = []
    for part in parts:
        if part.lower() in RESOLUTIONS:
            break
        result.append(part)
    return result


def _format_clean_name(parts):
    """Join title segments and wrap the trailing year token in parentheses.

    Expects the last element of *parts* to be the four-digit year.  Validates
    the year, wraps it, then joins the remaining tokens with spaces.

    :param parts: List of name segments where the final element is the year.
    :type parts: list
    :returns: Human-readable title string in ``Title Words (YYYY)`` format.
    :rtype: str
    """
    if len(parts) < 2 or not YEAR_RE.match(parts[-1]):
        return None

    title_parts = [part for part in parts[:-1] if part]
    if not title_parts:
        return None

    return '{} ({})'.format(' '.join(title_parts), parts[-1])


def _clean_scene_stem(name):
    """Return a clean scene-style name stem, or *name* if invalid."""
    if '.' not in name:
        return name
    parts = _strip_encoding_tags(name.split('.'))
    cleaned = _format_clean_name(parts)
    return cleaned if cleaned is not None else name


def folderNameCleaner(name):
    """Return a clean folder name derived from a scene-style dot-separated name.

    If the name contains no dots it is returned unchanged.  Otherwise,
    resolution tags and everything after them are stripped, and the year
    is wrapped in parentheses.

    :param name: The raw folder name to clean (e.g.
        ``Movie.Name.2023.1080p.BluRay``).
    :type name: str
    :returns: Cleaned folder name (e.g. ``Movie Name (2023)``), or *name*
        unchanged if it contains no dots.
    :rtype: str
    """
    return _clean_scene_stem(name)


def fileNameCleaner(name):
    """Return a clean file name derived from a scene-style dot-separated name.

    Behaves like :func:`folderNameCleaner` but preserves the original file
    extension.  If the name contains no dots it is returned unchanged.

    :param name: The raw file name to clean (e.g.
        ``Movie.Name.2023.1080p.BluRay.mkv``).
    :type name: str
    :returns: Cleaned file name with extension (e.g.
        ``Movie Name (2023).mkv``), or *name* unchanged if it contains no dots.
    :rtype: str
    """
    stem, extension = os.path.splitext(name)
    if not extension or '.' not in stem:
        return name
    cleaned = _clean_scene_stem(stem)
    return cleaned + extension if cleaned != stem else name


def _path_key(path):
    """Return a normalized path key for collision checks."""
    return os.path.normcase(os.path.abspath(path))


def _validate_plan(operations):
    """Ensure planned destination paths are unique and currently available."""
    destinations = {}
    for operation in operations:
        src_key = _path_key(operation.src)
        dst_key = _path_key(operation.dst)
        if dst_key in destinations and dst_key != src_key:
            raise RenamePlanError(
                'multiple renames target the same path: {}'.format(operation.dst)
            )
        destinations[dst_key] = operation

        if os.path.lexists(operation.dst) and dst_key != src_key:
            raise RenamePlanError(
                'destination already exists: {}'.format(operation.dst)
            )


def build_rename_plan(source):
    """Build and validate all file and folder rename operations for *source*."""
    if not os.path.isdir(source):
        raise RenamePlanError('"{}" is not a valid directory.'.format(source))

    operations = []
    for path in sorted(os.listdir(source)):
        full_path = os.path.join(source, path)
        if not os.path.isdir(full_path):
            continue

        for item in sorted(os.listdir(full_path)):
            if item.lower() in SKIP_NAMES:
                continue
            new_file_name = fileNameCleaner(item)
            if new_file_name != item:
                operations.append(RenameOperation(
                    os.path.join(source, path, item),
                    os.path.join(source, path, new_file_name),
                    'file'
                ))

        new_folder_name = folderNameCleaner(path)
        if new_folder_name != path:
            operations.append(RenameOperation(
                os.path.join(source, path),
                os.path.join(source, new_folder_name),
                'folder'
            ))

    _validate_plan(operations)
    return operations


def _is_case_only_rename(src, dst):
    """Return ``True`` for a rename that only changes path casing."""
    return (
        _path_key(src) == _path_key(dst)
        and os.path.abspath(src) != os.path.abspath(dst)
    )


def _temporary_path_for(path):
    """Return a non-existing temporary path next to *path*."""
    directory = os.path.dirname(path)
    basename = os.path.basename(path)
    while True:
        candidate = os.path.join(
            directory,
            '.mrenamer-{}-{}'.format(uuid4().hex, basename)
        )
        if not os.path.lexists(candidate):
            return candidate


def _rename_path(src, dst):
    """Rename *src* to *dst*, handling case-only renames portably."""
    if _is_case_only_rename(src, dst):
        temporary = _temporary_path_for(src)
        os.rename(src, temporary)
        try:
            os.rename(temporary, dst)
        except OSError:
            os.rename(temporary, src)
            raise
    else:
        os.rename(src, dst)


def _rollback(applied):
    """Best-effort rollback for already-applied rename operations."""
    rollback_errors = []
    for operation in reversed(applied):
        try:
            _rename_path(operation.dst, operation.src)
        except OSError as exc:
            rollback_errors.append('{}: {}'.format(operation.dst, exc))
    return rollback_errors


def renamer(source, dry_run=False):
    """Rename all movie folders and their files under *source*.

    For each immediate subdirectory of *source*, renames every file inside
    it (skipping entries in :data:`SKIP_NAMES`) using :func:`fileNameCleaner`,
    then renames the subdirectory itself using :func:`folderNameCleaner`.

    :param source: Path to the root directory containing movie folders.
    :type source: str
    :param dry_run: When ``True``, print planned renames but do not apply them.
    :type dry_run: bool
    :returns: Structured result describing planned and applied renames.
    :rtype: RenameResult
    """
    try:
        operations = build_rename_plan(source)
    except RenamePlanError as exc:
        return RenameResult(False, [], dry_run, str(exc))

    applied = []
    for operation in operations:
        if not dry_run:
            try:
                _rename_path(operation.src, operation.dst)
                applied.append(operation)
            except OSError as exc:
                rollback_errors = _rollback(applied)
                error = str(exc)
                if rollback_errors:
                    error = '{}; rollback errors: {}'.format(
                        error,
                        '; '.join(rollback_errors)
                    )
                return RenameResult(False, operations, dry_run, error)

    return RenameResult(True, operations, dry_run)


def format_rename_result(result):
    """Return human-readable output for a :class:`RenameResult`."""
    if not result.success:
        return 'Error: {}'.format(result.error)

    action = 'Would rename' if result.dry_run else 'Renamed'
    lines = ['{} item(s): {}'.format(action, len(result.operations))]
    for operation in result.operations:
        lines.append('{} {} -> {}'.format(
            '[dry-run]' if result.dry_run else operation.kind,
            os.path.basename(operation.src),
            os.path.basename(operation.dst)
        ))
    return '\n'.join(lines)


def main():
    """Entry point for mrenamer."""
    source = input('Source Directory: ')
    preview = input('Preview renames before applying? [y/n]: ').strip().lower()
    if preview == 'y':
        print('\n--- Dry run ---')
        result = renamer(source, dry_run=True)
        print(format_rename_result(result))
        if not result:
            sys.exit(1)
        confirm = input('\nProceed with renames? [y/n]: ').strip().lower()
        if confirm != 'y':
            print('Aborted.')
            sys.exit(0)

    result = renamer(source)
    print(format_rename_result(result))
    if not result:
        sys.exit(1)


if __name__ == '__main__':
    main()
