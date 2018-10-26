#!/usr/bin/env python
"""Test lddwrap."""
# pylint: disable=missing-docstring,too-many-public-methods
import pathlib
import unittest
from typing import Optional

import lddwrap


def dependencies_equal(dep: lddwrap.Dependency,
                       other: lddwrap.Dependency) -> bool:
    # Do not compare mem_address as it can differ between machines.
    return dep.soname == other.soname and \
           dep.path == other.path and \
           dep.found == other.found and \
           dep.unused == other.unused


class TestLdd(unittest.TestCase):
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
                mem_address="",
                unused=None),
            lddwrap.Dependency(
                soname=None,
                path=pathlib.Path("/lib64/ld-linux-x86-64.so.2"),
                found=True,
                mem_address="",
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
                mem_address="",
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
                mem_address="",
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

            self.assertTrue(
                dependencies_equal(dep, expected_deps[i]),
                "Incorrect dependency read from the line {}, expected {}\n"
                "got {}".format(line, expected_deps[i], dep))

    def test_parse_wrong_line(self):
        # ``parse_line`` raises a RuntimeError when it receives an unexpected
        # structured line
        run_err = None  # type: Optional[RuntimeError]
        line = "some wrong data which does not make sense"
        try:
            lddwrap._parse_line(line=line)  # pylint: disable=protected-access
        except RuntimeError as err:
            run_err = err

        self.assertIsNotNone(run_err)
        self.assertEqual(
            'Expected 2 parts in the line but found {}: {}'.format(
                line.count(' ') + 1, line), str(run_err))

    def test_pwd(self):
        path = pathlib.Path("/bin/pwd")
        deps = lddwrap.list_dependencies(path=path)

        expected_deps = [
            lddwrap.Dependency(
                soname="linux-vdso.so.1",
                path=None,
                found=True,
                mem_address="",
                unused=None),
            lddwrap.Dependency(
                soname="libc.so.6",
                path=pathlib.Path("/lib/x86_64-linux-gnu/libc.so.6"),
                found=True,
                mem_address="",
                unused=None),
            lddwrap.Dependency(
                soname=None,
                path=pathlib.Path("/lib64/ld-linux-x86-64.so.2"),
                found=True,
                mem_address="",
                unused=None)
        ]

        for dep in deps:
            for exp_dep in expected_deps:
                if exp_dep.soname == dep.soname:
                    self.assertTrue(
                        dependencies_equal(dep, exp_dep),
                        "Incorrect dependency, expected {}\ngot {}".format(
                            exp_dep, dep))
                    break

    def test_dir(self):
        path = pathlib.Path("/bin/dir")
        deps = lddwrap.list_dependencies(path=path)

        expected_deps = [
            lddwrap.Dependency(
                soname="linux-vdso.so.1",
                path=None,
                found=True,
                mem_address="",
                unused=None),
            lddwrap.Dependency(
                soname="libselinux.so.1",
                path=pathlib.Path("/lib/x86_64-linux-gnu/libselinux.so.1"),
                found=True,
                mem_address="",
                unused=None),
            lddwrap.Dependency(
                soname="libc.so.6",
                path=pathlib.Path("/lib/x86_64-linux-gnu/libc.so.6"),
                found=True,
                mem_address="",
                unused=None),
            lddwrap.Dependency(
                soname="libpcre.so.3",
                path=pathlib.Path("/lib/x86_64-linux-gnu/libpcre.so.3"),
                found=True,
                mem_address="",
                unused=None),
            lddwrap.Dependency(
                soname="libdl.so.2",
                path=pathlib.Path("/lib/x86_64-linux-gnu/libdl.so.2"),
                found=True,
                mem_address="",
                unused=None),
            lddwrap.Dependency(
                soname=None,
                path=pathlib.Path("/lib64/ld-linux-x86-64.so.2"),
                found=True,
                mem_address="",
                unused=None),
            lddwrap.Dependency(
                soname="libpthread.so.0",
                path=pathlib.Path("/lib/x86_64-linux-gnu/libpthread.so.0"),
                found=True,
                mem_address="",
                unused=None)
        ]

        for dep in deps:
            for exp_dep in expected_deps:
                if exp_dep.soname == dep.soname:
                    self.assertTrue(
                        dependencies_equal(dep, exp_dep),
                        "Incorrect dependency, expected {}\ngot {}".format(
                            exp_dep, dep))
                    break

    def test_dir_unused(self):
        path = pathlib.Path("/bin/dir")
        deps = lddwrap.list_dependencies(path=path, unused=True)

        expected_deps = [
            lddwrap.Dependency(
                soname="linux-vdso.so.1",
                path=None,
                found=True,
                mem_address="",
                unused=False),
            lddwrap.Dependency(
                soname="libselinux.so.1",
                path=pathlib.Path("/lib/x86_64-linux-gnu/libselinux.so.1"),
                found=True,
                mem_address="",
                unused=True),
            lddwrap.Dependency(
                soname="libc.so.6",
                path=pathlib.Path("/lib/x86_64-linux-gnu/libc.so.6"),
                found=True,
                mem_address="",
                unused=False),
            lddwrap.Dependency(
                soname="libpcre.so.3",
                path=pathlib.Path("/lib/x86_64-linux-gnu/libpcre.so.3"),
                found=True,
                mem_address="",
                unused=False),
            lddwrap.Dependency(
                soname="libdl.so.2",
                path=pathlib.Path("/lib/x86_64-linux-gnu/libdl.so.2"),
                found=True,
                mem_address="",
                unused=False),
            lddwrap.Dependency(
                soname=None,
                path=pathlib.Path("/lib64/ld-linux-x86-64.so.2"),
                found=True,
                mem_address="",
                unused=False),
            lddwrap.Dependency(
                soname="libpthread.so.0",
                path=pathlib.Path("/lib/x86_64-linux-gnu/libpthread.so.0"),
                found=True,
                mem_address="",
                unused=False)
        ]

        for dep in deps:
            for exp_dep in expected_deps:
                if exp_dep.soname == dep.soname:
                    self.assertTrue(
                        dependencies_equal(dep, exp_dep),
                        "Incorrect dependency, expected {}\ngot {}".format(
                            exp_dep, dep))
                    break


if __name__ == '__main__':
    unittest.main()
