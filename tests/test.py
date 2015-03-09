# -*- coding: utf-8 -*-

import logging
# import random
# import string
# import StringIO

# from docker_registry.core import driver
# from docker_registry.core import exceptions
from docker_registry import testing

# from nose import tools

logger = logging.getLogger(__name__)


class TestQuery(testing.Query):
    def __init__(self):
        self.scheme = 'cassandra'


class TestDriver(testing.Driver):
    def __init__(self):
        self.scheme = 'cassandra'
        self.path = ''
        self.config = testing.Config({})

#     @tools.raises(exceptions.FileNotFoundError)
#     def test_remove_inexistent_path(self):
#         filename = self.gen_random_string()
#         self._storage.remove("/".join((filename, filename)))


# class TestWriteStreaming(object):
#     def __init__(self):
#         self.scheme = 'cassandra'
#         self.path = ''
#         self.config = testing.Config({'elliptics_nodes': GOOD_REMOTE})

#     def setUp(self):
#         storage = driver.fetch(self.scheme)
#         self._storage = storage(self.path, self.config)

#     def gen_random_string(self, length=16):
#         return ''.join([random.choice(string.ascii_uppercase + string.digits)
#                         for x in range(length)]).lower()

#     def test_s_stream_write_many_chunks(self):
#         # decrease buffer size to
#         self._storage.buffer_size = 100
#         filename = self.gen_random_string(length=10)
#         path = "/".join((filename, filename))
#         fakedata = self.gen_random_string(length=201)
#         fakefile = StringIO.StringIO(fakedata)
#         self._storage.stream_write(path, fakefile)
#         assert self._storage.get_content(path) == fakedata


def _set_up_with_config(config):
    config = testing.Config(config)
    d = testing.Driver(scheme='cassandra',
                       config=config)
    d.setUp()
    return d
