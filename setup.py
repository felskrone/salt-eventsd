#!/usr/bin/env python
'''
The setup script for salteventsd
'''

import os
# Use setuptools only if the user opts-in by setting the USE_SETUPTOOLS env var
# This ensures consistent behavior but allows for advanced usage with
# virtualenv, buildout, and others.
USE_SETUPTOOLS = False
if 'USE_SETUPTOOLS' in os.environ:
    try:
        from setuptools import setup
        USE_SETUPTOOLS = True
    except:
        USE_SETUPTOOLS = False


if USE_SETUPTOOLS is False:
    from distutils.core import setup


# pylint: disable-msg=W0122,E0602
exec(compile(open('salteventsd/version.py').read(), 'salteventsd/version.py', 'exec'))
VERSION = __version__
# pylint: enable-msg=W0122,E0602

NAME = 'salt-eventsd'
DESC = ("Daemon that collects events from the salt-event-bus and writes them into a database")

kwargs = dict()

kwargs.update(
    name=NAME,
    version=VERSION,
    description=DESC,
    author='Volker Schwicking',
    author_email='vs@hosteurope.de',
    url='http://saltstack.org',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Topic :: System :: Distributed Computing'],
    packages=['salteventsd'],
    data_files=[('share/man/man1',
        ['doc/man/salt-eventsd.1']),
        ('share/man/man5',
        ['doc/man/salt-eventsd.5'])],
    scripts=['scripts/salt-eventsd'],
)

if USE_SETUPTOOLS:
    kwargs.update(
        install_requires=open('requirements.txt').readlines(),
        test_suite='tests',
    )

setup(**kwargs)

