#!/usr/bin/env python
# vim: set et ts=4 sw=4 fileencoding=utf-8:
'''
Setup script for yalp_grok
'''
import os
from setuptools import setup, find_packages

# Ensure we are in the yalp_grok source dir
SETUP_DIRNAME = os.path.dirname(__file__)
if SETUP_DIRNAME != '':
    os.chdir(SETUP_DIRNAME)

VERSION_FILE = os.path.join(os.path.abspath(SETUP_DIRNAME),
                            'yalp_grok',
                            'version.py')
REQ_FILE = os.path.join(os.path.abspath(SETUP_DIRNAME), 'requirements.txt')

# pylint: disable=W0122
exec(compile(open(VERSION_FILE).read(), VERSION_FILE, 'exec'))
# pylint: enable=W0122

VER = __version__  # pylint: disable=E0602

REQUIREMENTS = []
with open(REQ_FILE) as rfh:
    for line in rfh.readlines():
        if not line or line.startswith('#'):
            continue
        REQUIREMENTS.append(line.strip())


SETUP_KWARGS = {
    'name': 'yalp_grok',
    'version': VER,
    'url': 'https://github.com/yalp/yalp-grok',
    'license': 'MIT',
    'description': ('A Python library to parse strings and extract '
                    'information from structured/unstructured data'),
    'author': 'Timothy Messier',
    'author_email': 'tim.messier@gmail.com',
    'classifiers': [
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],
    'packages': find_packages(exclude=[
        '*.tests*', '*.tests.*', 'tests.*', 'tests',
    ]),
    # 'package_data': {
    #     'yalp_gork': [
    #         'LICENSE',
    #         'README.rst',
    #         'tests/*',
    #         'yalp_grok/patterns/*',
    #         'requirements.txt',
    #         'dev_requirements.txt',
    #     ],
    # },
    'include_package_data': True,
    'data_files': [],
    'install_requires': REQUIREMENTS,
}

if __name__ == '__main__':
    setup(**SETUP_KWARGS)
