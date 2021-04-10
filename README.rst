pylddwrap
=========
.. image:: https://github.com/Parquery/pylddwrap/actions/workflows/ci.yml/badge.svg?branch=master
    :target: https://github.com/Parquery/pylddwrap/actions/workflows/ci.yml?query=branch%3Amaster
    :alt: Build Status

.. image:: https://coveralls.io/repos/github/Parquery/pylddwrap/badge.svg?branch=master
    :target: https://coveralls.io/github/Parquery/pylddwrap?branch=master
    :alt: Coverage

.. image:: https://badges.frapsoft.com/os/mit/mit.png?v=103
    :target: https://opensource.org/licenses/mit-license.php
    :alt: MIT License

.. image:: https://badge.fury.io/py/pylddwrap.svg
    :target: https://badge.fury.io/py/pylddwrap
    :alt: PyPI - version

.. image:: https://img.shields.io/pypi/pyversions/pylddwrap.svg
    :alt: PyPI - Python Version

.. image:: https://readthedocs.org/projects/pylddwrap/badge/?version=latest
    :target: https://pylddwrap.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

Pylddwrap wraps ldd \*nix utility to determine shared libraries required by a program.

We need to dynamically package subset of our system at deployment time. Consequently, we have to determine the
dependencies on shared libraries of our binaries programmatically.

The output of ldd Linux command, while informative, is not structured enough to be easily integrated into a program.
At the time of this writing, we only found two alternative ldd wrappers on Internet
`python-ldd <https://github.com/relip/python-ldd>`_ and `ldd.py <https://gist.github.com/masami256/1588876>`_, but their
output was either too basic for our use case or the project was still incipient.

Pylddwrap, in contrast, returns a well-structured list of the dependencies. The command-line tool outputs the
dependencies either as a table (for visual inspection) or as a JSON-formatted string (for use with other tools).
The included Python module lddwrap returns a Python object with type annotations so that it can be used readily by the
deployment scripts and other modules.

For more information on the ldd tool, please see `ldd manual <http://man7.org/linux/man-pages/man1/ldd.1.html>`_.

Usage
=====

Command-Line Tool pylddwrap
---------------------------

* Assume we need the dependencies of the /bin/ls. The following command gives them as a table:

.. code-block:: bash

    pylddwrap /bin/ls

* The output of the command looks like this:

.. code-block:: text

    soname          | path                                  | found | mem_address        | unused
    ----------------+---------------------------------------+-------+--------------------+-------
    linux-vdso.so.1 | None                                  | True  | 0x00007ffd8750f000 | False
    libselinux.so.1 | /lib/x86_64-linux-gnu/libselinux.so.1 | True  | 0x00007f4e73dc3000 | True
    libc.so.6       | /lib/x86_64-linux-gnu/libc.so.6       | True  | 0x00007f4e739f9000 | False
    libpcre.so.3    | /lib/x86_64-linux-gnu/libpcre.so.3    | True  | 0x00007f4e73789000 | False
    libdl.so.2      | /lib/x86_64-linux-gnu/libdl.so.2      | True  | 0x00007f4e73585000 | False
    None            | /lib64/ld-linux-x86-64.so.2           | True  | 0x00007f4e73fe5000 | False
    libpthread.so.0 | /lib/x86_64-linux-gnu/libpthread.so.0 | True  | 0x00007f4e73368000 | False


* To obtain the dependencies as JSON, invoke:

.. code-block:: bash

    pylddwrap --format json /bin/ls

* The JSON output is structured like this:

.. code-block:: text

  [
    {
      "soname": "linux-vdso.so.1",
      "path": "None",
      "found": true,
      "mem_address": "0x00007ffed857f000",
      "unused": false
    },
    ...
  ]

* You can also sort the table with ``--sorted`` which will sort by ``soname``:

.. code-block:: bash

    pylddwrap /bin/pwd --sorted

* Pylddwrap gives the table sorted by ``soname``:

.. code-block:: text

    soname          | path                            | found | mem_address        | unused
    ----------------+---------------------------------+-------+--------------------+-------
    None            | /lib64/ld-linux-x86-64.so.2     | True  | 0x00007fd54894d000 | False
    libc.so.6       | /lib/x86_64-linux-gnu/libc.so.6 | True  | 0x00007fd548353000 | False
    linux-vdso.so.1 | None                            | True  | 0x00007ffe0953f000 | False

Alternatively, you can sort by any other column. For example, to sort
by ``path``:

.. code-block:: bash

    pylddwrap /bin/pwd --sorted path

* The output will be:

.. code-block:: text

    soname          | path                            | found | mem_address        | unused
    ----------------+---------------------------------+-------+--------------------+-------
    linux-vdso.so.1 | None                            | True  | 0x00007ffe0953f000 | False
    libc.so.6       | /lib/x86_64-linux-gnu/libc.so.6 | True  | 0x00007fd548353000 | False
    None            | /lib64/ld-linux-x86-64.so.2     | True  | 0x00007fd54894d000 | False


ldwrap Python Module
--------------------

We provide lddwrap Python module which you can integrate into your deployment scripts and other modules.

* The following example shows how to list the dependencies of /bin/ls:

.. code-block:: python

    import pathlib
    import lddwrap

    path = pathlib.Path("/bin/ls")
    deps = lddwrap.list_dependencies(path=path)
    for dep in deps:
        print(dep)

    """
    soname: linux-vdso.so.1, path: None, found: True, mem_address: (0x00007ffe8e2fb000), unused: None
    soname: libselinux.so.1, path: /lib/x86_64-linux-gnu/libselinux.so.1, found: True, mem_address: (0x00007f7759ccc000), unused: None
    soname: libc.so.6, path: /lib/x86_64-linux-gnu/libc.so.6, found: True, mem_address: (0x00007f7759902000), unused: None
    ...
    """

* List all dependencies of the /bin/ls utility and check if the direct dependencies are used.
  If unused for list_dependencies is set to False then the unused variable of the dependencies will not be determined
  and are therefore unknown and set to None. Otherwise information about direct usage will be retrieved and added to the
  dependencies.

.. code-block:: python

    import pathlib
    import lddwrap

    path = pathlib.Path("/bin/ls")
    deps = lddwrap.list_dependencies(path=path, unused=True)
    print(deps[1])
    # soname: libselinux.so.1,
    # path: /lib/x86_64-linux-gnu/libselinux.so.1,
    # found: True,
    # mem_address: (0x00007f5a6064a000),
    # unused: True

* Lddwrap operates normally with the environment variables of the caller. In cases where your dependencies are
  determined differently than the current environment, you pass a separate environment (in form of a dictionary) as an argument:

.. code-block:: python

    import os
    import pathlib
    import lddwrap

    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = "some/important/path"
    path = pathlib.Path("/bin/ls")
    deps = lddwrap.list_dependencies(path=path, env=env)

Installation
============

* Install pylddwrap with pip:

.. code-block:: bash

    pip3 install pylddwrap


Development
===========

* Check out the repository.

* In the repository root, create the virtual environment:

.. code-block:: bash

    python3 -m venv venv3

* Activate the virtual environment:

.. code-block:: bash

    source venv3/bin/activate

* Install the development dependencies:

.. code-block:: bash

    pip3 install -e .[dev]

* Tests can be run directly using ``unittest``:

.. code-block:: bash

    python3 -m unittest discover tests/


Pre-commit Checks
-----------------

We provide a set of pre-commit checks that lint and check code for formatting.

Namely, we use:

* `yapf <https://github.com/google/yapf>`_ to check the formatting.
* The style of the docstrings is checked with `pydocstyle <https://github.com/PyCQA/pydocstyle>`_.
* Static type analysis is performed with `mypy <http://mypy-lang.org/>`_.
* Various linter checks are done with `pylint <https://www.pylint.org/>`_.


Apply the automatic formatting by running the ``format`` environment:

.. code-block:: bash

    tox -e format

Run the pre-commit checks and tests using ``tox``:

.. code-block:: bash

    tox


Versioning
==========
We follow `Semantic Versioning <http://semver.org/spec/v1.0.0.html>`_. The version X.Y.Z indicates:

* X is the major version (backward-incompatible),
* Y is the minor version (backward-compatible), and
* Z is the patch version (backward-compatible bug fix).
