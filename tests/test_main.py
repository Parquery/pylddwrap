#!/usr/bin/env python3
"""Test the main routine."""

import io
import json
import pathlib
import textwrap
import unittest
from typing import List, TextIO, cast

import lddwrap
import lddwrap.main
import pylddwrap_meta

# pylint: disable=missing-docstring
import tests


class TestParseArgs(unittest.TestCase):
    def test_single_path(self):
        args = lddwrap.main.parse_args(
            sys_argv=['some-executable.py', '/bin/ls'])
        self.assertEqual(pathlib.Path('/bin/ls'), args.path)

    def test_format(self):
        args = lddwrap.main.parse_args(
            sys_argv=['some-executable.py', '/bin/ls', "--format", "json"])
        self.assertEqual("json", args.format)


class TestMain(unittest.TestCase):
    # pylint: disable=protected-access
    def test_verbose(self):
        deps = []  # type: List[lddwrap.Dependency]
        for index in range(3):
            deps.append(
                lddwrap.Dependency(
                    found=True,
                    soname='lib{}.so'.format(index),
                    path=pathlib.Path('/bin/lib{}.so'.format(index)),
                    mem_address=hex(index),
                    unused=False))

        buf = io.StringIO()
        stream = cast(TextIO, buf)
        lddwrap._output_verbose(deps=deps, stream=stream)
        # pylint: disable=trailing-whitespace
        expected_output = textwrap.dedent("""\
        soname  | path         | found | mem_address | unused
        --------+--------------+-------+-------------+-------
        lib0.so | /bin/lib0.so | True  | 0x0         | False 
        lib1.so | /bin/lib1.so | True  | 0x1         | False 
        lib2.so | /bin/lib2.so | True  | 0x2         | False """)

        output = textwrap.dedent(buf.getvalue())
        self.assertEqual(expected_output, output)

    def test_json(self):
        deps = []  # type: List[lddwrap.Dependency]
        for index in range(2):
            deps.append(
                lddwrap.Dependency(
                    found=True,
                    soname='lib{}.so'.format(index),
                    path=pathlib.Path('/bin/lib{}.so'.format(index)),
                    mem_address=hex(index),
                    unused=False))

        buf = io.StringIO()
        stream = cast(TextIO, buf)
        lddwrap._output_json(deps=deps, stream=stream)

        expected_output = textwrap.dedent("""\
            [
              {
                "soname": "lib0.so",
                "path": "/bin/lib0.so",
                "found": true,
                "mem_address": "0x0",
                "unused": false
              },
              {
                "soname": "lib1.so",
                "path": "/bin/lib1.so",
                "found": true,
                "mem_address": "0x1",
                "unused": false
              }
            ]""")

        output = textwrap.dedent(buf.getvalue())
        self.assertEqual(expected_output, output)

    def test_json_format(self):
        deps = []  # type: List[lddwrap.Dependency]
        for index in range(2):
            deps.append(
                lddwrap.Dependency(
                    found=True,
                    soname='lib{}.so'.format(index),
                    path=pathlib.Path('/bin/lib{}.so'.format(index)),
                    mem_address=hex(index),
                    unused=False))

        buf = io.StringIO()
        stream = cast(TextIO, buf)

        json.dump(obj=[dep.as_mapping() for dep in deps], fp=stream, indent=2)
        try:
            json.loads(buf.getvalue())
        except ValueError:
            self.fail("The following data was not in json format\n\n{}".format(
                buf.getvalue()))

    def test_main(self):
        buf = io.StringIO()
        stream = cast(TextIO, buf)

        args = lddwrap.main.parse_args(
            sys_argv=["some-executable.py", "/bin/pwd"])

        with tests.MockLdd(
                out="\n".join([
                    "\tlinux-vdso.so.1 (0x00007ffe0953f000)",
                    "\tlibc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007fd548353000)",  # pylint: disable=C0301
                    "\t/lib64/ld-linux-x86-64.so.2 (0x00007fd54894d000)",
                    "",
                ]),
                out_unused=''):

            retcode = lddwrap.main._main(args=args, stream=stream)

            self.assertEqual(0, retcode)
            # pylint: disable=trailing-whitespace
            expected_output = textwrap.dedent("""\
            soname          | path                            | found | mem_address        | unused
            ----------------+---------------------------------+-------+--------------------+-------
            linux-vdso.so.1 | None                            | True  | 0x00007ffe0953f000 | False 
            libc.so.6       | /lib/x86_64-linux-gnu/libc.so.6 | True  | 0x00007fd548353000 | False 
            None            | /lib64/ld-linux-x86-64.so.2     | True  | 0x00007fd54894d000 | False 
            """)
            output = textwrap.dedent(buf.getvalue())

            self.assertEqual(expected_output, output)

    def test_sorted_without_specific_attribute(self):
        buf = io.StringIO()
        stream = cast(TextIO, buf)

        args = lddwrap.main.parse_args(
            sys_argv=["some-executable.py", "/bin/pwd", "--sorted"])

        with tests.MockLdd(
                out="\n".join([
                    "\tlinux-vdso.so.1 (0x00007ffe0953f000)",
                    "\tlibc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007fd548353000)",  # pylint: disable=C0301
                    "\t/lib64/ld-linux-x86-64.so.2 (0x00007fd54894d000)",
                    "",
                ]),
                out_unused=''):

            retcode = lddwrap.main._main(args=args, stream=stream)

            self.assertEqual(0, retcode)
            # pylint: disable=trailing-whitespace
            expected_output = textwrap.dedent("""\
            soname          | path                            | found | mem_address        | unused
            ----------------+---------------------------------+-------+--------------------+-------
            None            | /lib64/ld-linux-x86-64.so.2     | True  | 0x00007fd54894d000 | False 
            libc.so.6       | /lib/x86_64-linux-gnu/libc.so.6 | True  | 0x00007fd548353000 | False 
            linux-vdso.so.1 | None                            | True  | 0x00007ffe0953f000 | False 
            """)
            output = textwrap.dedent(buf.getvalue())

            self.assertEqual(expected_output, output)

    def test_sorted_with_specific_attribute(self):
        buf = io.StringIO()
        stream = cast(TextIO, buf)

        args = lddwrap.main.parse_args(
            sys_argv=["some-executable.py", "/bin/pwd", "--sorted", "path"])

        with tests.MockLdd(
                out="\n".join([
                    "\tlinux-vdso.so.1 (0x00007ffe0953f000)",
                    "\tlibc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007fd548353000)",  # pylint: disable=C0301
                    "\t/lib64/ld-linux-x86-64.so.2 (0x00007fd54894d000)",
                ]),
                out_unused=''):

            retcode = lddwrap.main._main(args=args, stream=stream)

            self.assertEqual(0, retcode)
            # pylint: disable=trailing-whitespace
            expected_output = textwrap.dedent("""\
            soname          | path                            | found | mem_address        | unused
            ----------------+---------------------------------+-------+--------------------+-------
            linux-vdso.so.1 | None                            | True  | 0x00007ffe0953f000 | False 
            libc.so.6       | /lib/x86_64-linux-gnu/libc.so.6 | True  | 0x00007fd548353000 | False 
            None            | /lib64/ld-linux-x86-64.so.2     | True  | 0x00007fd54894d000 | False 
            """)
            output = textwrap.dedent(buf.getvalue())

            self.assertEqual(expected_output, output)

    def test_version(self):
        with self.assertRaises(SystemExit):
            buf = io.StringIO()
            stream = cast(TextIO, buf)
            args = lddwrap.main.parse_args(
                sys_argv=["some-executable.py", "--version"])

            retcode = lddwrap.main._main(args=args, stream=stream)
            self.assertEqual(0, retcode)
            self.assertEqual('{}\n'.format(pylddwrap_meta.__version__),
                             buf.getvalue())


if __name__ == '__main__':
    unittest.main()
