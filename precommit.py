#!/usr/bin/env python3
"""Runs precommit checks on the repository."""
import argparse
import os
import pathlib
import shutil
import subprocess
import sys
import sysconfig
import textwrap

# os.fspath() is 3.6+.  str is a reasonable substitute
# https://docs.python.org/3.9/library/os.html#os.fspath
fspath = getattr(os, "fspath", str)


class ToxNotFoundError(Exception):
    """Rasie when tox not found in expected locations."""


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--overwrite",
        help=
        "Overwrites the unformatted source files with the well-formatted code in place. "  # pylint: disable=line-too-long
        "If not set, an exception is raised if any of the files do not conform to the style guide.",  # pylint: disable=line-too-long
        action='store_true')

    args = parser.parse_args()

    tox_environments = ["check", "_auto_version"]

    if args.overwrite:
        tox_environments.insert(0, "format")

    tox_from_path = shutil.which("tox")

    maybe_scripts = sysconfig.get_path("scripts")
    tox_from_scripts = pathlib.Path(maybe_scripts).joinpath(
        "tox") if maybe_scripts is not None else None

    if tox_from_path is not None:
        tox = pathlib.Path(tox_from_path)
    elif tox_from_scripts is not None and tox_from_scripts.is_file():
        tox = tox_from_scripts
    else:
        message = textwrap.dedent(f'''\
        'tox' executable not found in PATH or scripts directory
            PATH: {os.environ['PATH']}
            scripts: {maybe_scripts}
        ''')
        raise ToxNotFoundError(message)

    repo_root = pathlib.Path(__file__).parent

    tox_ini = repo_root.joinpath("tox.ini")

    command = [
        fspath(tox), "-c",
        fspath(tox_ini), "-e", ",".join(tox_environments)
    ]
    completed_process = subprocess.run(command)  # pylint: disable=W1510

    return completed_process.returncode


if __name__ == "__main__":
    sys.exit(main())
