#!/usr/bin/env python3
"""Determine shared libraries required by a program."""

# This file is necessary so that we can specify the entry point for pex.

import argparse
import pathlib
import sys
from typing import Any, List, TextIO

import lddwrap
import pylddwrap_meta


class Args:
    """Represent parsed command-line arguments."""

    def __init__(self, args: Any) -> None:
        """Initialize with arguments parsed with ``argparse``."""
        self.format = str(args.format)
        self.path = pathlib.Path(args.path)
        self.sort_by = (None if args.sort_by is None else str(args.sort_by))


def parse_args(sys_argv: List[str]) -> Args:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-v",
        "--version",
        help="Display the version and return immediately",
        action='version',
        version=pylddwrap_meta.__version__ + "\n")
    parser.add_argument(
        "-f",
        "--format",
        help="Specify the output format.",
        default='verbose',
        choices=['verbose', 'json'])
    parser.add_argument(
        '-s',
        '--sorted',
        # ``sorted`` is reserved for a built-in method, so we need to pick
        # a different identifier.
        dest='sort_by',
        help='If set, the output is sorted by the given attribute',
        const='soname',
        choices=lddwrap.DEPENDENCY_ATTRIBUTES,
        nargs='?')

    parser.add_argument("path", help="Specify path to the binary")

    args = parser.parse_args(sys_argv[1:])

    if pathlib.Path(args.path).is_dir():
        parser.error("Path '{}' is a dir. Path to file required. Check out "
                     "--help for more information.".format(args.path))

    if not pathlib.Path(args.path).is_file():
        parser.error(
            "Path '{}' is not a file. Path to file required. Check out "
            "--help for more information.".format(args.path))

    return Args(args=args)


def _main(args: Args, stream: TextIO) -> int:
    """Execute the main routine."""
    # pylint: disable=protected-access
    deps = lddwrap.list_dependencies(path=args.path, unused=True)

    if args.sort_by is not None:
        lddwrap._sort_dependencies_in_place(deps=deps, sort_by=args.sort_by)

    if args.format == 'verbose':
        lddwrap._output_verbose(deps=deps, stream=stream)
    elif args.format == 'json':
        lddwrap._output_json(deps=deps, stream=stream)
    else:
        raise NotImplementedError("Unhandled format: {}".format(args.format))
    stream.write('\n')

    return 0


def main() -> None:
    """Wrap the main routine so that it can be tested."""
    args = parse_args(sys_argv=sys.argv)
    sys.exit(_main(args=args, stream=sys.stdout))
