#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import setuptools
except ImportError:
    import distutils.core as setuptools

__author__ = 'Milaw'
__copyright__ = 'Copyright 2015'
# __credits__ = []
__version__ = '0.1.4'
__maintainer__ = 'Milaw'
__email__ = 'gmilaw@gmail.com'
__title__ = 'docker-registry-driver-cassandra'
__build__ = 0x000000
__url__ = 'https://github.com/milaw/docker-registry-driver-cassandra'
__d__ = 'https://github.com/milaw/docker-registry-driver-cassandra/archive/master.zip'
__description__ = 'Docker registry driver for cassandra'

setuptools.setup(
    name=__title__,
    version=__version__,
    author=__author__,
    author_email=__email__,
    maintainer=__maintainer__,
    maintainer_email=__email__,
    url=__url__,
    download_url=__d__,
    description=__description__,
    classifiers=['Development Status :: 3 - Alpha',
                 'Intended Audience :: Developers',
                 'Programming Language :: Python',
                 'Operating System :: OS Independent',
                 'Topic :: Utilities'],
    platforms=['Independent'],
    package_data = {'docker_registry': ['../config/*']},
    license=open('./LICENSE').read(),
    namespace_packages=['docker_registry', 'docker_registry.drivers'],
    packages=['docker_registry', 'docker_registry.drivers'],
    install_requires=open('./requirements.txt').read(),
    zip_safe=True,
    tests_require=open('./tests/requirements.txt').read(),
    test_suite='nose.collector'
)
