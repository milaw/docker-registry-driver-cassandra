#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import setuptools
except ImportError:
    import distutils.core as setuptools


__author__ = 'Milaw'
__copyright__ = 'Copyright 2015'
__credits__ = []

__version__ = '0.1.0'
__maintainer__ = 'Milaw'
__email__ = 'gmilaw@gmail.com'

__title__ = 'docker-registry-driver-cassandra'
__build__ = 0x000000

__url__ = 'https://github.com/milaw/docker-registry-driver-cassandra'
__description__ = 'Docker registry driver for cassandra'

setuptools.setup(
    name=__title__,
    version=__version__,
    author=__author__,
    author_email=__email__,
    maintainer=__maintainer__,
    maintainer_email=__email__,
    url=__url__,
    description=__description__,
    classifiers=['Development Status :: Beta',
                 'Intended Audience :: Developers',
                 'Programming Language :: Python',
                 'Operating System :: OS Independent',
                 'Topic :: Utilities'],
    platforms=['Independent'],
    namespace_packages=['docker_registry', 
                        'docker_registry.drivers', 
                        'docker_registry.contrib'],
    packages=['docker_registry', 
              'docker_registry.drivers', 
              'docker_registry.contrib', 
              'docker_registry.contrib.cassandra'],
    package_data = {'docker_registry': ['../config/*']},
    install_requires=[
        "docker-registry-core>=2,<3",
        "filechunkio"
    ],
    zip_safe=True
    #tests_require=[
    #    "nose==1.3.3",
    #    "coverage==3.7.1",
    #],
    #test_suite='nose.collector'
)