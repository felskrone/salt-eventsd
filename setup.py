#!/usr/bin/env python
'''
The setup script for salteventsd
'''

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import salteventsd

with open('README.md') as f:
    readme = f.read()

setup(
    name='salt-eventsd',
    version=salteventsd.__version__,
    description="Daemon that collects events from the salt-event-bus and writes them into any backend, mysql, redis, etc.",
    long_description=readme,
    author='Volker Schwicking',
    author_email='vs@hosteurope.de',
    url='https://github.com/felskrone/salt-eventsd',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Topic :: System :: Distributed Computing'],
    install_requires=open('requirements.txt').readlines(),
    packages=['salteventsd'],
    keywords = ['saltstack', 'salt'],
    data_files=[
        ('share/man/man1', ['doc/man/salt-eventsd.1']),
        ('share/man/man5', ['doc/man/salt-eventsd.5']),
    ],
    scripts=['scripts/salt-eventsd'],
)
