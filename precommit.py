#!/usr/bin/env python3
"""Runs precommit checks on the repository."""
import argparse
import os
import pathlib
import subprocess
import sys


def main() -> int:
    """"
    Execute the main routine.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--overwrite",
        help=
        "Overwrites the unformatted source files with the well-formatted code in place. "  # pylint: disable=line-too-long
        "If not set, an exception is raised if any of the files do not conform to the style guide.",  # pylint: disable=line-too-long
        action='store_true')

    args = parser.parse_args()

    overwrite = bool(args.overwrite)

    repo_root = pathlib.Path(__file__).parent
    # yapf: disable
    print("YAPF'ing...")
    if overwrite:
        subprocess.check_call([
            "yapf", "--in-place", "--style=style.yapf", "--recursive", "tests",
            "lddwrap", "setup.py", "precommit.py", "bin/pylddwrap"
        ], cwd=str(repo_root))
    else:
        subprocess.check_call([
            "yapf", "--diff", "--style=style.yapf", "--recursive", "tests",
            "lddwrap", "setup.py", "precommit.py", "bin/pylddwrap"
        ], cwd=str(repo_root))

    print("Mypy'ing...")
    subprocess.check_call(["mypy", "lddwrap", "tests", "bin/pylddwrap"],
                          cwd=str(repo_root))

    print("Isort'ing...")
    if overwrite:
        subprocess.check_call([
            "isort", "--recursive", "tests", "lddwrap",
            "bin/pylddwrap"], cwd=str(repo_root))
    else:
        subprocess.check_call([
            "isort", "--check-only", "--recursive", "tests", "lddwrap",
            "bin/pylddwrap"], cwd=str(repo_root))

    print("Pylint'ing...")
    subprocess.check_call(
        ["pylint", "--rcfile=pylint.rc", "tests", "lddwrap", "bin/pylddwrap"],
        cwd=str(repo_root))

    print("Pydocstyle'ing...")
    subprocess.check_call(["pydocstyle", "lddwrap", "bin/pylddwrap"],
                          cwd=str(repo_root))

    print("Testing...")
    env = os.environ.copy()
    env['ICONTRACT_SLOW'] = 'true'

    subprocess.check_call([
        "coverage", "run", "--source", "lddwrap", "-m", "unittest", "discover",
        "tests"
    ], cwd=str(repo_root))

    subprocess.check_call(["coverage", "report"])

    # yapf: enable
    print("Doctesting...")
    subprocess.check_call(
        [sys.executable, "-m", "doctest",
         str(repo_root / "README.rst")])
    for pth in (repo_root / "lddwrap").glob("**/*.py"):
        subprocess.check_call([sys.executable, "-m", "doctest", str(pth)])

    print("pyicontract-lint'ing...")
    for pth in (repo_root / "lddwrap").glob("**/*.py"):
        subprocess.check_call(["pyicontract-lint", str(pth)])

    print("Checking the restructured text of the readme...")
    subprocess.check_call(
        ['python3', 'setup.py', 'check', '--restructuredtext', '--strict'])

    return 0


if __name__ == "__main__":
    sys.exit(main())
