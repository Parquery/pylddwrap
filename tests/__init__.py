"""Test lddwrap."""

import os
import shlex
import tempfile
import textwrap
from typing import Optional


class MockLdd:
    """Manage context for a mock ldd script."""

    def __init__(self, out: str, out_unused: str) -> None:
        self._tmpdir = None  # type: Optional[tempfile.TemporaryDirectory]
        self.out = out
        self.out_unused = out_unused
        self._old_path = None  # type: Optional[str]

    def __enter__(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()

        # Create a mock bach script called ``ldd`` based on
        # https://github.com/lattera/glibc/blob/master/elf/ldd.bash.in
        script = textwrap.dedent('''\
        #!/usr/bin/env bash
        if [ $# -eq 1 ]; then
            echo {out}
        elif [ "$1" = "--unused" ]; then
            echo {out_unused}

            # Return code 1 implies at least one unused dependency.
            exit 1
        else
            >&2 echo '$0 is: ' $0
            >&2 echo '$1 is: ' $1
            >&2 echo '$2 is: ' $2
            >&2 echo "Unhandled command line arguments (count: $#): $@"
            exit 1984
        fi
        '''.format(
            out=shlex.quote(self.out), out_unused=shlex.quote(self.out_unused)))

        pth = os.path.join(self._tmpdir.name, 'ldd')
        with open(pth, 'wt') as fid:
            fid.write(script)

        os.chmod(pth, 0o700)

        self._old_path = os.environ.get('PATH', None)

        os.environ['PATH'] = (self._tmpdir.name if self._old_path is None else
                              self._tmpdir.name + os.pathsep + self._old_path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._tmpdir.cleanup()
        if self._old_path is None:
            del os.environ['PATH']
        else:
            os.environ['PATH'] = self._old_path
