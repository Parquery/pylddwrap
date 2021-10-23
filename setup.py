"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""
import os

import pylddwrap_meta
from setuptools import find_packages, setup

# pylint: disable=redefined-builtin

here = os.path.abspath(os.path.dirname(__file__))  # pylint: disable=invalid-name

with open(os.path.join(here, 'README.rst'), encoding='utf-8') as fid:
    long_description = fid.read().strip()  # pylint: disable=invalid-name

with open(os.path.join(here, 'requirements.txt'), encoding='utf-8') as fid:
    install_requires = [
        line for line in fid.read().splitlines() if line.strip()
    ]

setup(
    name=pylddwrap_meta.__title__,
    version=pylddwrap_meta.__version__,
    description=pylddwrap_meta.__description__,
    long_description=long_description,
    url=pylddwrap_meta.__url__,
    author=pylddwrap_meta.__author__,
    author_email=pylddwrap_meta.__author_email__,
    # yapf: disable
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    # yapf: enable
    license='License :: OSI Approved :: MIT License',
    keywords='ldd dependency dependencies lddwrap pylddwrap',
    packages=find_packages(exclude=['tests']),
    python_requires='>=3.6',
    install_requires=install_requires,
    extras_require={
        'dev': [
            # yapf: disable
            'mypy==0.790; implementation_name != "pypy"',
            'pylint==2.6.0',
            'yapf==0.24.0',
            'tox>=3.0.0',
            'coverage>=5.5.0,<6',
            'diff-cover>=5.0.1,<6; python_version >= "3.6"',
            'isort<5',
            'pydocstyle>=3.0.0,<4',
            'pyicontract-lint>=2.0.0,<3',
            'docutils>=0.14,<1',
            'pygments>=2.2.0,<3'
            # yapf: enable
        ]
    },
    scripts=['bin/pylddwrap'],
    py_modules=['lddwrap', 'pylddwrap_meta'],
    package_data={"lddwrap": ["py.typed"]},
    data_files=[('.', ['LICENSE', 'README.rst', 'requirements.txt'])])
