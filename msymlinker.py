#!/usr/bin/env python3
"""msymlinker — Creates soft symlinks from a new location back to the original."""

import os
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class LinkResult:
    """Structured result for symlink creation."""

    success: bool
    original: str
    link: str
    error: str = ''

    def __bool__(self):
        return self.success


def linker(src, old_name, dest_dir, new_name):
    """Create a soft symlink pointing from *dest_dir/new_name* to *src/old_name*.

    The symlink target is the absolute path of the original file or folder,
    so it remains valid regardless of the working directory at access time.

    :param src: Directory containing the original file or folder.
    :type src: str
    :param old_name: Name of the original file or folder inside *src*.
    :type old_name: str
    :param dest_dir: Directory where the symlink will be created.
    :type dest_dir: str
    :param new_name: Name for the new symlink inside *dest_dir*.
    :type new_name: str
    :returns: Structured result describing the created or failed symlink.
    :rtype: LinkResult
    """
    original = os.path.abspath(os.path.join(src, old_name))
    link = os.path.abspath(os.path.join(dest_dir, new_name))

    if not os.path.exists(original):
        return LinkResult(False, original, link,
                          'source path does not exist: {}'.format(original))

    if not os.path.isdir(dest_dir):
        return LinkResult(False, original, link,
                          'destination directory does not exist: {}'.format(dest_dir))

    if os.path.lexists(link):
        return LinkResult(False, original, link,
                          'a file or symlink already exists at: {}'.format(link))

    try:
        os.symlink(original, link)
        return LinkResult(True, original, link)
    except (OSError, PermissionError) as e:
        return LinkResult(False, original, link, 'error creating symlink: {}'.format(e))


def format_link_result(result):
    """Return human-readable output for a :class:`LinkResult`."""
    if result.success:
        return 'Linked {} -> {}'.format(result.link, result.original)
    return 'Error: {}'.format(result.error)


def main():
    """Entry point for msymlinker."""
    src = input('Source directory (where the original folder lives): ')
    old_name = input('Original folder name: ')
    dest_dir = input('Destination directory (where the symlink will be created): ')
    new_name = input('Symlink name: ')

    result = linker(src, old_name, dest_dir, new_name)
    print(format_link_result(result))
    if result:
        print('Complete.')
    else:
        print('Something went wrong.')
        sys.exit(1)


if __name__ == '__main__':
    main()
