#!/usr/bin/env python3
"""Wrap ldd *nix utility to determine shared libraries required by a program."""

import collections
import copy
import json
import pathlib
import re
import subprocess
# pylint: disable=unused-import
from typing import Any, Dict, List, Mapping, Optional, TextIO

import icontract

DEPENDENCY_ATTRIBUTES = ['soname', 'path', 'found', 'mem_address', 'unused']


# yapf: disable
@icontract.invariant(
    lambda self: not (self.soname is None and self.found) or (
            self.path is not None and self.mem_address is not None)
)
@icontract.invariant(
    lambda self: not (self.path is None and self.found) or (
            self.soname is not None and self.mem_address is not None)
)
@icontract.invariant(
    lambda self: not (self.mem_address is None and self.found) or (
            self.soname is not None and self.path is not None)
)
# yapf: enable
class Dependency:
    """
    Represent a shared library required by a program.

    :ivar found: True if ``ldd`` could resolve the library
    :vartype found: bool

    :ivar soname: library name
    :vartype soname: Optional[str]

    :ivar path: path to the library
    :vartype path: Optional[pathlib.Path]

    :ivar mem_address: hex memory location
    :vartype mem_address: Optional[str]

    :ivar unused: library not used
    :vartype unused: Optional[bool]
    """

    @icontract.ensure(
        lambda self: all(hasattr(self, col) for col in DEPENDENCY_ATTRIBUTES),
        "All expected attributes are present so that "
        "lists of dependencies can be sorted dynamically")
    def __init__(self,
                 found: bool,
                 soname: Optional[str] = None,
                 path: Optional[pathlib.Path] = None,
                 mem_address: Optional[str] = None,
                 unused: Optional[bool] = None) -> None:
        """Initialize the dependency with the given values."""
        # pylint: disable= too-many-arguments
        self.soname = soname
        self.path = path
        self.found = found
        self.mem_address = mem_address
        self.unused = unused

    def __str__(self) -> str:
        """Transform the dependency to a human-readable format."""
        return "soname: {}, path: {}, found: {}, mem_address: {}, unused: {}" \
               "".format(self.soname, self.path, self.found,
                         self.mem_address, self.unused)

    # pylint: disable=unsubscriptable-object
    def as_mapping(self) -> Mapping[str, Any]:
        """
        Transform the dependency to a mapping.

        Can be converted to JSON and similar formats.
        """
        return collections.OrderedDict([("soname", self.soname),
                                        ("path", str(self.path)),
                                        ("found", self.found),
                                        ("mem_address", self.mem_address),
                                        ("unused", self.unused)])


_MEM_ADDRESS_RE = re.compile(r'^\s*\(([^)]*)\)\s*$')


def _strip_mem_address(text: str) -> str:
    r"""
    Strip the space and brackets from the mem address in the output.

    :param text: to be stripped
    :return: bare mem address

    >>> _strip_mem_address('(0x00007f9a1a329000)')
    '0x00007f9a1a329000'

    >>> _strip_mem_address(' (0x00007f9a1a329000) ')
    '0x00007f9a1a329000'

    >>> _strip_mem_address('\t(0x00007f9a1a329000)\t')
    '0x00007f9a1a329000'
    """
    mtch = _MEM_ADDRESS_RE.match(text)
    if not mtch:
        raise RuntimeError(("Unexpected mem address. Expected to match {}, "
                            "but got: {!r}").format(_MEM_ADDRESS_RE.pattern,
                                                    text))

    return mtch.group(1)


def _parse_line(line: str) -> Optional[Dependency]:
    """
    Parse single line of ldd output.

    :param line: to parse
    :return: dependency or None if line was empty

    """
    found = not 'not found' in line
    parts = [part.strip() for part in line.split(' ')]
    # pylint: disable=line-too-long
    # There are two types of outputs for a dependency, with or without soname.
    # The VDSO is a special case (see https://man7.org/linux/man-pages/man7/vdso.7.html)
    #
    # For example:
    # VDSO (Ubuntu 16.04): linux-vdso.so.1 =>  (0x00007ffd7c7fd000)
    # VDSO (Ubuntu 18.04): linux-vdso.so.1 (0x00007ffe2f993000)
    # with soname: 'libstdc++.so.6 => /usr/lib/x86_64-linux-gnu/libstdc++.so.6 (0x00007f9a19d8a000)'
    # without soname: '/lib64/ld-linux-x86-64.so.2 (0x00007f9a1a329000)'
    # with soname but not found: 'libboost_program_options.so.1.62.0 => not found'
    # with soname but without rpath: 'linux-vdso.so.1 =>  (0x00007ffd7c7fd000)'
    # pylint: enable=line-too-long
    if '=>' in line:
        if len(parts) != 4:
            raise RuntimeError(
                "Expected 4 parts in the line but found {}: {}".format(
                    len(parts), line))

        soname = None
        dep_path = None
        mem_address = None
        if found:
            soname = parts[0]
            if parts[2] != '':
                dep_path = pathlib.Path(parts[2])

            mem_address = _strip_mem_address(text=parts[3])
        else:
            if "/" in parts[0]:
                dep_path = pathlib.Path(parts[0])
            else:
                soname = parts[0]

        return Dependency(
            soname=soname, path=dep_path, found=found, mem_address=mem_address)
    else:
        if len(parts) != 2:
            # Please see https://github.com/Parquery/pylddwrap/pull/14
            if 'no version information available' in line:
                return None

            raise RuntimeError(
                "Expected 2 parts in the line but found {}: {}".format(
                    len(parts), line))

        if parts[0].startswith('linux-vdso'):
            soname = parts[0]
            path = None
        else:
            soname = None
            path = pathlib.Path(parts[0])

        return Dependency(
            soname=soname,
            path=path,
            found=True,
            mem_address=_strip_mem_address(text=parts[1]))


@icontract.require(lambda path: path.is_file())
def list_dependencies(path: pathlib.Path,
                      unused: bool = False,
                      env: Optional[Dict[str, str]] = None) -> List[Dependency]:
    """
    Retrieve a list of dependencies of the given binary.

    >>> path = pathlib.Path("/bin/ls")
    >>> deps = list_dependencies(path=path)
    >>> deps[0].soname
    'linux-vdso.so.1'

    :param path: path to a file
    :param unused:
        if set, check if dependencies are actually used by the program
    :param env:
        the environment to use.

        If ``env`` is None, currently active env will be used.
        Otherwise specified env is used.
    :return: list of dependencies
    """
    # We need to use /usr/bin/env since Popen ignores the PATH,
    # see https://stackoverflow.com/questions/5658622
    proc = subprocess.Popen(
        ["/usr/bin/env", "ldd", path.as_posix()],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env=env)

    out, err = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(
            "Failed to ldd external libraries of {} with code {}:\nout:\n{}\n\n"
            "err:\n{}".format(path, proc.returncode, out, err))

    dependencies = _cmd_output_parser(cmd_out=out)  # type: List[Dependency]

    if unused:
        proc_unused = subprocess.Popen(
            ["/usr/bin/env", "ldd", "--unused",
             path.as_posix()],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            env=env)

        out_unused, err_unused = proc_unused.communicate()
        # return code = 0 -> no unused dependencies,
        # return code = 1 -> some unused dependencies
        if proc_unused.returncode not in [0, 1]:
            raise RuntimeError(
                "Failed to ldd external libraries of {} with code {}:\nout:\n"
                "{}\n\nerr:\n{}".format(path, proc.returncode, out_unused,
                                        err_unused))

        dependencies = _update_unused(
            dependencies=dependencies, out_unused=out_unused)

    return dependencies


def _cmd_output_parser(cmd_out: str) -> List[Dependency]:
    """
    Parse the command line output.

    :param cmd_out: command line output
    :return: List of dependencies
    """
    dependencies = []  # type: List[Dependency]

    lines = [line.strip() for line in cmd_out.split('\n') if line.strip() != '']

    if len(lines) == 0:
        return []

    # Static libraries can appear in multiple forms:
    # - a first line refering to the library and a second line indicating
    #   that the library was statically linked,
    # - only a single line indicating statically linked.
    # See: https://github.com/Parquery/pylddwrap/issues/12
    if 1 <= len(lines) <= 2 and lines[-1] == 'statically linked':
        return []

    for line in lines:
        dep = _parse_line(line=line)
        if dep is not None:
            dependencies.append(dep)

    return dependencies


def _update_unused(dependencies: List[Dependency],
                   out_unused: str) -> List[Dependency]:
    """
    Set "unused" property of the dependencies.

    Updates the "unused" property of the dependencies using the output string
    from ldd command.

    :param dependencies: List of dependencies
    :param out_unused: output from command ldd --unused
    :return: updated list of dependencies
    """
    unused_dependencies = []  # type: List[pathlib.Path]

    for line in [
            line.strip() for line in out_unused.split('\n')
            if line.strip() != ''
    ]:
        # skip first line because it's no dependency
        if line != "Unused direct dependencies:":
            unused_dependencies.append(pathlib.Path(line.strip()))

    for dep in dependencies:
        dep.unused = dep.path in unused_dependencies

    return dependencies


# pylint: disable=unnecessary-lambda
@icontract.require(lambda sort_by: sort_by in DEPENDENCY_ATTRIBUTES)
@icontract.snapshot(
    lambda deps: copy.copy(deps), name='deps', enabled=icontract.SLOW)
@icontract.ensure(
    lambda deps, OLD: set(deps) == set(OLD.deps), enabled=icontract.SLOW)
# pylint: enable=line-too-long
def _sort_dependencies_in_place(deps: List[Dependency], sort_by: str) -> None:
    """Order the dependencies by the given ``sort_by`` attribute."""
    if len(deps) < 2:
        return

    def compute_key(dep: Dependency) -> str:
        """Produce key for the sort."""
        assert hasattr(dep, sort_by)
        key = getattr(dep, sort_by)

        assert key is None or isinstance(key, (bool, str, pathlib.Path))

        if key is None:
            return ''

        return str(key)

    deps.sort(key=compute_key)


def _output_verbose(deps: List[Dependency], stream: TextIO) -> None:
    """
    Output dependencies in verbose, human-readable format to the ``stream``.

    :param deps: list of dependencies
    :param stream: output stream
    :return:
    """
    table = [["soname", "path", "found", "mem_address", "unused"]]

    for dep in deps:
        table.append([
            str(dep.soname),
            str(dep.path),
            str(dep.found),
            str(dep.mem_address),
            str(dep.unused)
        ])

    stream.write(_format_table(table))


def _output_json(deps: List[Dependency], stream: TextIO) -> None:
    """
    Output dependencies in a JSON format to the ``stream``.

    :param deps: list of dependencies
    :param stream: output stream
    :return:
    """
    json.dump(obj=[dep.as_mapping() for dep in deps], fp=stream, indent=2)


@icontract.require(
    lambda table: not table or all(len(row) == len(table[0]) for row in table))
@icontract.ensure(lambda table, result: result == "" if not table else True)
@icontract.ensure(lambda result: not result.endswith("\n"))
def _format_table(table: List[List[str]]) -> str:
    """
    Format the table as equal-spaced columns.

    :param table: rows of cells
    :return: table as string
    """
    cols = len(table[0])

    col_widths = [max(len(row[i]) for row in table) for i in range(cols)]

    lines = []  # type: List[str]
    for i, row in enumerate(table):
        parts = []  # type: List[str]

        for cell, width in zip(row, col_widths):
            parts.append(cell.ljust(width))

        line = " | ".join(parts)
        lines.append(line)

        if i == 0:
            border = []  # type: List[str]

            for width in col_widths:
                border.append("-" * width)

            lines.append("-+-".join(border))

    result = "\n".join(lines)

    return result
