# -*- coding: utf-8 -*-
"""
Created on Mon Sep 21 21:20:30 2026

@author: dcr
"""

import re
import os



def is_windows_path(path: str) -> bool:
    """
    Detect whether a given path is a Windows-style path.

    Returns True for:
        C:\\Users\\foo
        C:/Users/foo
        C:foo                 (drive-relative)
        \\\\server\\share\\file   (UNC)
        \\\\?\\C:\\very\\long\\path  (extended-length)
        \\\\.\\COM1              (device path)

    Returns False for:
        /cygdrive/c/Users/foo
        /usr/bin
        relative/path
        foo\\bar              (relative, no drive/UNC)
    """
    if not path or not isinstance(path, str):
        return False

    # UNC path: \\server\share\...  (also covers \\?\ and \\.\ prefixes)
    if path.startswith("\\\\") or path.startswith("//"):
        return True

    # Drive-letter path: C:\... , C:/... , or C:relative
    if re.match(r"^[a-zA-Z]:", path):
        return True

    return False


def classify_path(path: str) -> str:
    """
    Classify a path as 'windows', 'cygwin', or 'unknown'.
    """
    if is_windows_path(path):
        return "windows"
    if is_cygwin_path(path):     # from the previous answer
        return "cygwin"
    return "unknown"

def is_cygwin_path(path: str) -> bool:
    """
    Detect whether a given path is a Cygwin-style path.

    Cygwin paths look like:
        /cygdrive/c/Users/foo
        /cygdrive/d/Projects/bar

    Also returns True for plain POSIX paths that start with '/'
    (e.g. '/usr/bin') since those are valid Cygwin paths too.
    """
    if not path or not isinstance(path, str):
        return False

    # Normalize backslashes just in case
    normalized = path.replace("\\", "/")

    # Explicit Cygwin drive mount: /cygdrive/<letter>/...
    if re.match(r"^/cygdrive/[a-zA-Z](/|$)", normalized):
        return True

    # Generic POSIX-style absolute path (also valid under Cygwin)
    if normalized.startswith("/"):
        return True

    return False


def windows_to_cygwin(path: str) -> str:
    """
    Convert a Windows path into a Cygwin path.

    Examples:
        C:\\Users\\foo\\bar      -> /cygdrive/c/Users/foo/bar
        D:/Projects/test.txt    -> /cygdrive/d/Projects/test.txt
        \\\\server\\share\\file   -> //server/share/file   (UNC)
    """
    if not path or not isinstance(path, str):
        raise ValueError("Path must be a non-empty string")

    # Normalize separators
    p = path.replace("\\", "/")

    # Handle UNC paths (\\server\share\...)
    if p.startswith("//"):
        return p  # Cygwin accepts //server/share/... as-is

    # Handle drive-letter paths: C:/...  or  C:...
    match = re.match(r"^([a-zA-Z]):(.*)$", p)
    if match:
        drive = match.group(1).lower()
        rest = match.group(2)
        if not rest.startswith("/"):
            rest = "/" + rest
        return f"/cygdrive/{drive}{rest}"

    # Relative or already POSIX path — just return normalized form
    return p