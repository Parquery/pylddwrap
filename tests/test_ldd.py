#!/usr/bin/env python
"""Test lddwrap."""
# pylint: disable=missing-docstring,too-many-public-methods
import pathlib
import tempfile
import unittest
from typing import Any, List, Optional

import lddwrap

import tests


class DependencyDiff:
    """Represent a different between two dependencies."""

    def __init__(self, attribute: str, ours: Any, theirs: Any) -> None:
        self.attribute = attribute
        self.ours = ours
        self.theirs = theirs

    def __repr__(self) -> str:
        return "DependencyDiff(attribute={!r}, ours={!r}, theirs={!r})".format(
            self.attribute, self.ours, self.theirs)


def diff_dependencies(ours: lddwrap.Dependency,
                      theirs: lddwrap.Dependency) -> List[DependencyDiff]:
    """
    Compare two dependencies and give their differences in a list.

    An empty list means no difference.
    """
    keys = sorted(ours.__dict__.keys())
    assert keys == sorted(theirs.__dict__.keys())

    result = []  # type: List[DependencyDiff]
    for key in keys:
        if ours.__dict__[key] != theirs.__dict__[key]:
            result.append(
                DependencyDiff(
                    attribute=key,
                    ours=ours.__dict__[key],
                    theirs=theirs.__dict__[key]))

    return result


class TestParseOutputWithoutUnused(unittest.TestCase):
    def test_parse_line(self):
        # yapf: disable
        lines = [
            "libstdc++.so.6 => /usr/lib/x86_64-linux-gnu/libstdc++.so.6 "
            "(0x00007f9a19d8a000)",
            "/lib64/ld-linux-x86-64.so.2 (0x00007f9a1a329000)",
            "libboost_program_options.so.1.62.0 => not found",
            "linux-vdso.so.1 =>  (0x00007ffd7c7fd000)",
            "libopencv_stitching.so.3.3 => not found",
            "libstdc++.so.6 => /usr/lib/x86_64-linux-gnu/libstdc++.so.6 "
            "(0x00007f4b78462000)",
            "libz.so.1 => not found",
            "../build/debug/libextstr.so => not found",
            "/home/user/lib/liblmdb.so => not found"
        ]
        # yapf: enable

        expected_deps = [
            lddwrap.Dependency(
                soname="libstdc++.so.6",
                path=pathlib.Path("/usr/lib/x86_64-linux-gnu/libstdc++.so.6"),
                found=True,
                mem_address="0x00007f9a19d8a000",
                unused=None),
            lddwrap.Dependency(
                soname=None,
                path=pathlib.Path("/lib64/ld-linux-x86-64.so.2"),
                found=True,
                mem_address="0x00007f9a1a329000",
                unused=None),
            lddwrap.Dependency(
                soname="libboost_program_options.so.1.62.0",
                path=None,
                found=False,
                mem_address=None,
                unused=None),
            lddwrap.Dependency(
                soname="linux-vdso.so.1",
                path=None,
                found=True,
                mem_address="0x00007ffd7c7fd000",
                unused=None),
            lddwrap.Dependency(
                soname="libopencv_stitching.so.3.3",
                path=None,
                found=False,
                mem_address=None,
                unused=None),
            lddwrap.Dependency(
                soname="libstdc++.so.6",
                path=pathlib.Path("/usr/lib/x86_64-linux-gnu/libstdc++.so.6"),
                found=True,
                mem_address="0x00007f4b78462000",
                unused=None),
            lddwrap.Dependency(
                soname="libz.so.1", path=None, found=False, mem_address=None),
            lddwrap.Dependency(
                soname=None,
                path=pathlib.Path("../build/debug/libextstr.so"),
                found=False,
                mem_address=None,
                unused=None),
            lddwrap.Dependency(
                soname=None,
                path=pathlib.Path("/home/user/lib/liblmdb.so"),
                found=False,
                mem_address=None,
                unused=None)
        ]

        for i, line in enumerate(lines):
            # pylint: disable=protected-access
            dep = lddwrap._parse_line(line=line)

            self.assertListEqual(
                [], diff_dependencies(ours=dep, theirs=expected_deps[i]),
                "Incorrect dependency read from the line {} {!r}".format(
                    i + 1, line))

    def test_parse_wrong_line(self):
        # ``parse_line`` raises a RuntimeError when it receives an unexpected
        # structured line
        run_err = None  # type: Optional[RuntimeError]
        line = "\tsome wrong data which does not make sense"
        try:
            lddwrap._parse_line(line=line)  # pylint: disable=protected-access
        except RuntimeError as err:
            run_err = err

        self.assertIsNotNone(run_err)
        self.assertEqual(
            'Expected 2 parts in the line but found {}: {}'.format(
                line.count(' ') + 1, line), str(run_err))

    def test_parse_non_indented_line(self):
        """Lines without leading indentation, at this point in processing, are
        informational.
        """
        # https://github.com/Parquery/pylddwrap/pull/14
        line = (
            "qt/6.0.2/gcc_64/plugins/sqldrivers/libqsqlpsql.so:" +
            " /lib/x86_64-linux-gnu/libpq.so.5:" +
            " no version information available" +
            " (required by qt/6.0.2/gcc_64/plugins/sqldrivers/libqsqlpsql.so)")
        result = lddwrap._parse_line(line=line)  # pylint: disable=protected-access

        self.assertIsNone(result)

    def test_parse_static(self) -> None:
        """Test parsing of the output when we ldd a static library."""
        # pylint: disable=protected-access
        deps = lddwrap._cmd_output_parser("\n".join([
            "my_static_lib.so:",
            "    statically linked",
            "",
        ]))

        self.assertListEqual([], deps)


class TestAgainstMockLdd(unittest.TestCase):
    def test_pwd(self):
        """Test parsing the captured output  of ``ldd`` on ``/bin/pwd``."""

        with tests.MockLdd(
                out="\n".join([
                    "\tlinux-vdso.so.1 (0x00007ffe0953f000)",
                    "\tlibc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007fd548353000)",  # pylint: disable=C0301  # pylint: disable=C0301
                    "\t/lib64/ld-linux-x86-64.so.2 (0x00007fd54894d000)",
                    "",
                ]),
                out_unused=''):
            deps = lddwrap.list_dependencies(
                path=pathlib.Path('/bin/pwd'), unused=False)

            expected_deps = [
                lddwrap.Dependency(
                    soname="linux-vdso.so.1",
                    path=None,
                    found=True,
                    mem_address="0x00007ffe0953f000",
                    unused=None),
                lddwrap.Dependency(
                    soname='libc.so.6',
                    path=pathlib.Path("/lib/x86_64-linux-gnu/libc.so.6"),
                    found=True,
                    mem_address="0x00007fd548353000",
                    unused=None),
                lddwrap.Dependency(
                    soname=None,
                    path=pathlib.Path("/lib64/ld-linux-x86-64.so.2"),
                    found=True,
                    mem_address="0x00007fd54894d000",
                    unused=None)
            ]

            self.assertEqual(len(expected_deps), len(deps))

            for i, (dep, expected_dep) in enumerate(zip(deps, expected_deps)):
                self.assertListEqual([],
                                     diff_dependencies(
                                         ours=dep, theirs=expected_dep),
                                     "Mismatch at the dependency {}".format(i))

    def test_bin_dir(self):
        """Test parsing the captured output  of ``ldd`` on ``/bin/dir``."""

        # pylint: disable=line-too-long
        with tests.MockLdd(
                out="\n".join([
                    "\tlinux-vdso.so.1 (0x00007ffd66ce2000)",
                    "\tlibselinux.so.1 => /lib/x86_64-linux-gnu/libselinux.so.1 (0x00007f72b88fc000)",
                    "\tlibc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f72b850b000)",
                    "\tlibpcre.so.3 => /lib/x86_64-linux-gnu/libpcre.so.3 (0x00007f72b8299000)",
                    "\tlibdl.so.2 => /lib/x86_64-linux-gnu/libdl.so.2 (0x00007f72b8095000)",
                    "\t/lib64/ld-linux-x86-64.so.2 (0x00007f72b8d46000)",
                    "\tlibpthread.so.0 => /lib/x86_64-linux-gnu/libpthread.so.0 (0x00007f72b7e76000)",
                    "",
                ]),
                out_unused=''):
            # pylint: enable=line-too-long
            deps = lddwrap.list_dependencies(
                path=pathlib.Path('/bin/dir'), unused=False)

            expected_deps = [
                lddwrap.Dependency(
                    soname="linux-vdso.so.1",
                    path=None,
                    found=True,
                    mem_address="0x00007ffd66ce2000",
                    unused=None),
                lddwrap.Dependency(
                    soname="libselinux.so.1",
                    path=pathlib.Path("/lib/x86_64-linux-gnu/libselinux.so.1"),
                    found=True,
                    mem_address="0x00007f72b88fc000",
                    unused=None),
                lddwrap.Dependency(
                    soname="libc.so.6",
                    path=pathlib.Path("/lib/x86_64-linux-gnu/libc.so.6"),
                    found=True,
                    mem_address="0x00007f72b850b000",
                    unused=None),
                lddwrap.Dependency(
                    soname="libpcre.so.3",
                    path=pathlib.Path("/lib/x86_64-linux-gnu/libpcre.so.3"),
                    found=True,
                    mem_address="0x00007f72b8299000",
                    unused=None),
                lddwrap.Dependency(
                    soname="libdl.so.2",
                    path=pathlib.Path("/lib/x86_64-linux-gnu/libdl.so.2"),
                    found=True,
                    mem_address="0x00007f72b8095000",
                    unused=None),
                lddwrap.Dependency(
                    soname=None,
                    path=pathlib.Path("/lib64/ld-linux-x86-64.so.2"),
                    found=True,
                    mem_address="0x00007f72b8d46000",
                    unused=None),
                lddwrap.Dependency(
                    soname="libpthread.so.0",
                    path=pathlib.Path("/lib/x86_64-linux-gnu/libpthread.so.0"),
                    found=True,
                    mem_address="0x00007f72b7e76000",
                    unused=None),
            ]

            self.assertEqual(len(expected_deps), len(deps))

            for i, (dep, expected_dep) in enumerate(zip(deps, expected_deps)):
                self.assertListEqual([],
                                     diff_dependencies(
                                         ours=dep, theirs=expected_dep),
                                     "Mismatch at the dependency {}".format(i))

    def test_bin_dir_with_empty_unused(self):
        # pylint: disable=line-too-long
        with tests.MockLdd(
                out="\n".join([
                    "\tlinux-vdso.so.1 (0x00007ffd66ce2000)",
                    "\tlibselinux.so.1 => /lib/x86_64-linux-gnu/libselinux.so.1 (0x00007f72b88fc000)",
                    "\tlibc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f72b850b000)",
                    "\tlibpcre.so.3 => /lib/x86_64-linux-gnu/libpcre.so.3 (0x00007f72b8299000)",
                    "\tlibdl.so.2 => /lib/x86_64-linux-gnu/libdl.so.2 (0x00007f72b8095000)",
                    "\t/lib64/ld-linux-x86-64.so.2 (0x00007f72b8d46000)",
                    "\tlibpthread.so.0 => /lib/x86_64-linux-gnu/libpthread.so.0 (0x00007f72b7e76000)",
                    "",
                ]),
                out_unused=''):
            # pylint: enable=line-too-long
            deps = lddwrap.list_dependencies(
                path=pathlib.Path("/bin/dir"), unused=True)

            unused = [dep for dep in deps if dep.unused]
            self.assertListEqual([], unused)

    def test_with_fantasy_unused(self):
        """Test against a fantasy executable with fantasy unused."""
        # pylint: disable=line-too-long
        with tests.MockLdd(
                out="\n".join([
                    "\tlinux-vdso.so.1 (0x00007ffd66ce2000)",
                    "\tlibm.so.6 => /lib64/libm.so.6 (0x00007f72b7e76000)",
                    "",
                ]),
                out_unused="\n".join([
                    "Unused direct dependencies:",
                    "\t/lib64/libm.so.6",
                    "",
                ]),
        ):
            # pylint: enable=line-too-long
            deps = lddwrap.list_dependencies(
                path=pathlib.Path("/bin/dir"), unused=True)

            unused = [dep for dep in deps if dep.unused]

            expected_unused = [
                lddwrap.Dependency(
                    soname="libm.so.6",
                    path=pathlib.Path("/lib64/libm.so.6"),
                    found=True,
                    mem_address="0x00007f72b7e76000",
                    unused=True)
            ]

            self.assertEqual(len(expected_unused), len(unused))

            for i, (dep, exp_dep) in enumerate(zip(unused, expected_unused)):
                self.assertListEqual(
                    [], diff_dependencies(ours=dep, theirs=exp_dep),
                    "Mismatch at the unused dependency {}".format(i))

    def test_with_static_library(self) -> None:
        """Test against a fantasy static library."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            lib_pth = pathlib.Path(tmp_dir) / "my_static_lib.so"
            lib_pth.write_text("totally static!")

            with tests.MockLdd(
                    out="\n".join([
                        "my_static_lib.so:",
                        "\tstatically linked",
                        "",
                    ]),
                    out_unused=''):
                # pylint: enable=line-too-long
                deps = lddwrap.list_dependencies(path=lib_pth, unused=True)

                # The dependencies are empty since the library is
                # statically linked.
                self.assertListEqual([], deps)


class TestSorting(unittest.TestCase):
    def test_sorting_by_all_attributes(self) -> None:
        # pylint: disable=line-too-long
        with tests.MockLdd(
                out="\n".join([
                    "\tlinux-vdso.so.1 (0x00007ffd66ce2000)",
                    "\tlibselinux.so.1 => /lib/x86_64-linux-gnu/libselinux.so.1 (0x00007f72b88fc000)",
                    "\tlibc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f72b850b000)",
                    "\tlibpcre.so.3 => /lib/x86_64-linux-gnu/libpcre.so.3 (0x00007f72b8299000)",
                    "\tlibdl.so.2 => /lib/x86_64-linux-gnu/libdl.so.2 (0x00007f72b8095000)",
                    "\t/lib64/ld-linux-x86-64.so.2 (0x00007f72b8d46000)",
                    "\tlibpthread.so.0 => /lib/x86_64-linux-gnu/libpthread.so.0 (0x00007f72b7e76000)",
                    "",
                ]),
                out_unused=''):
            # pylint: enable=line-too-long

            for attr in lddwrap.DEPENDENCY_ATTRIBUTES:
                deps = lddwrap.list_dependencies(
                    path=pathlib.Path("/bin/dir"), unused=True)

                # pylint: disable=protected-access
                lddwrap._sort_dependencies_in_place(deps=deps, sort_by=attr)

                previous = getattr(deps[0], attr)
                previous = '' if previous is None else str(previous)

                for i in range(1, len(deps)):
                    current = getattr(deps[i], attr)
                    current = '' if current is None else str(current)

                    self.assertLessEqual(
                        previous, current,
                        ("The dependencies must be sorted according to "
                         "attribute {!r}: {!r}").format(attr, deps))


if __name__ == '__main__':
    unittest.main()
