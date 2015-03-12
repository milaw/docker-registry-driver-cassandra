# to import cassandra from global namespace
# instead of local directory
from __future__ import absolute_import

import itertools
import logging
import time
import sys

# cassandra
from cassandra.cluster import Cluster
from cassandra.query import dict_factory
from cassandra.query import SimpleStatement
from cassandra.policies import DowngradingConsistencyRetryPolicy
from cassandra.policies import ConstantReconnectionPolicy
from cassandra.auth import PlainTextAuthProvider

# docker-registry
from docker_registry.core import driver
from docker_registry.core import exceptions
from docker_registry.core import lru

DEFAULT_KEYSPACE = "DockerKSpace"
DEFAULT_TABLE_NAME = DEFAULT_KEYSPACE + ".DockerImages"
DEFAUL_CLUSTERS_LIST = "127.0.0.1"
DEFAUL_CQL_VERSION = None
DEFAULT_PROTOCOL_VERSION = 2
DEFAULT_PORT = 9042
DEFAULT_COMPRESSION = True
DEFAULT_AUTHENTICATION_PROVIDER = False
DEFAULT_AUTHENTICATION_INFO = ''
DEFAULT_SESSION_TIMEOUT = 10
DEFAULT_SESSION_FETCH_SIZE = 5000

logger = logging.getLogger(__name__)

class Storage(driver.Base):

    def __init__(self, path=None, config=None):
        print 1
        # Turn on streaming support
        self.supports_bytes_range = True
        # Increase buffer size up to 640 Kb
        self.buffer_size = 128 * 1024
        # Create default Cassandra config
        self._root_path = config.storage_path or '/'

        self._clusters_list = (config.cassandra_clusters_list or
                               DEFAUL_CLUSTERS_LIST)
        # If a specific version of CQL should be used, otherwise, the highest
        # CQL version supported by the server will be automatically used
        self._cql_version = (config.cassandra_cql_version or
                             DEFAUL_CQL_VERSION)
        # The version of the native protocol to use
        self._protocol_version = (config.cassandra_protocol_version or
                                  DEFAULT_PROTOCOL_VERSION)
        # The server-side port to open connections to. Defaults to 9042
        self._port = config.cassandra_port or DEFAULT_PORT
        # Controls compression for communications between the driver
        # and Cassandra. If left as the default of True
        self._compression = (config.cassandra_compression or
                             DEFAULT_COMPRESSION)
        # Authentification
        self._authentication_provider = (config.cassandra_authentication_provider or
                                         DEFAULT_AUTHENTICATION_PROVIDER)
        self._authentication_username = (config.cassandra_authentication_username or
                                         DEFAULT_AUTHENTICATION_INFO)
        self._authentication_password = (config.cassandra_authentication_password or
                                         DEFAULT_AUTHENTICATION_INFO)
        # A default timeout, measured in seconds, for queries executed
        # through execute() or execute_async()
        # This timeout currently has no effect on callbacks registered
        # on a ResponseFuture through
        # ResponseFuture.add_callback() or ResponseFuture.add_errback();
        # even if a query exceeds this default timeout,
        # neither the registered callback or errback will be called.cluster
        self._session_timeout = (config.cassandra_session_timeout or
                                 DEFAULT_SESSION_TIMEOUT)
        # By default, this many rows will be fetched at a time.
        # Setting this to None will
        # disable automatic paging for large query results
        self._session_fetch_size = (config.cassandra_session_fetch_size or
                                    DEFAULT_SESSION_FETCH_SIZE)

        # default value is None. It means `do not use auth`
        auth_provider = None
        if self._authentication_provider:
            auth_provider = PlainTextAuthProvider(
                username=self._authentication_username,
                password=self._authentication_password)

        # The set of IP addresses we pass to the Cluster is simply an initial
        # set of contact points.
        # After the driver connects to one of these nodes
        # it will automatically discover the rest of
        # the nodes in the cluster and connect to them,
        # so you don't need to list every node in your cluster.
        raw_clusters_list = self._clusters_list
        if raw_clusters_list is None:
            raise exceptions.ConfigError("clusters_list must be specified")
        elif isinstance(raw_clusters_list, (tuple, list)):
            clusters_list = tuple(raw_clusters_list)
        elif isinstance(raw_clusters_list, (str, unicode)):
            # assume we have spaceseparated string
            clusters_list = tuple(raw_clusters_list.split())
        else:
            raise exceptions.ConfigError("clusters_list must be list,"
                                         "tuple or string")
        logger.debug("cluster list %s", str(clusters_list))
        self.cluster = Cluster(clusters_list,
                               port=self._port,
                               protocol_version=self._protocol_version,
                               auth_provider=auth_provider,
                               default_retry_policy=DowngradingConsistencyRetryPolicy(),
                               reconnection_policy=ConstantReconnectionPolicy(20.0, 10))
        
        self.metadata = self.cluster.metadata
        self.session = self.cluster.connect()
        
        for host in self.metadata.all_hosts():
            logger.info('Datacenter: %s; Host: %s',
                host.datacenter, host.address)

        self.create_schema()
        time.sleep(3)
        self.insert_data('test','success','first')
        self.select_data("test") 

    def create_schema(self):
        print 2
         # CREATE KEYSPACE
        self.session.execute("""
            CREATE KEYSPACE IF NOT EXISTS DockerKSpace
            WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 };
        """)
        logger.debug("KEYSPACE executed!")
        
        # CREATE TABLE
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS DockerKSpace.DockerImages (
                key varchar,
                value text,
                tag text,
                PRIMARY KEY (key) 
            ) WITH caching ='keys_only';
        """)
        logger.debug("TABLE executed!")

    def insert_data(self, key, value, tag):
        print 3
        insert_statement = self.session.prepare("""
            INSERT INTO DockerKSpace.DockerImages (key, value, tag)
            VALUES (?, ?, ?);
        """)
        self.session.execute(insert_statement.bind((key, value, tag)))
        logger.info("insert_data DONE")

    def select_data(self, key):
        print 4
        results = self.session.execute("""
            SELECT * FROM DockerKSpace.DockerImages WHERE key = 'test';
        """)
        #logger.debug("SELECT DONE")
        print "results : %s", results       

    def _init_path(self, path=None):
        print 5
        path = self._root_path + path if path else self._root_path
        logger.debug("Using path %s", path)
        return path

    def disconnect_to_cluster(self):
        print 6
        self.cluster.shutdown()
        self.session.shutdown()
        logger.info('Connection closed')

    def data_remove(self, key):
        print 8
        fail = False
        query = "DELETE FROM " + DEFAULT_TABLE_NAME + " WHERE key IN ('" + key + "');"
        rows = self.session.execute(query)
        if fail:
            raise exceptions.FileNotFoundError("No such file %s" % key)

    def data_read(self, path, offset=0, size=0):
        print 9
        query = "SELECT first_name, last_name FROM " + DEFAULT_TABLE_NAME + " WHERE empID IN (105, 107, 104);"
        rows = self.session.execute(query)
        return

    def data_write(self, key, value, tags):
        print 10
        fail = False
        query = "INSERT INTO " + DEFAULT_TABLE_NAME + " (key,value,tag) VALUES (" + key + "," + value + "," + tag + ") IF NOT EXISTS"
        rows = self.session.execute(query)
        if fail:
            raise exceptions.UnspecifiedError("Index setting failed %s" % err)

    def data_append(self, key, content):
        print 11
        fail = False
        if fail:
            raise exceptions.UnspecifiedError("Writing failed {0}".format(err))

    def data_write_file(self, path, content):
        print 12
        return

    def data_find(self, tags):
        print 13
        r = self._session.find_all_indexes(list(tags))
        r.wait()
        result = r.get()
        return [str(i.indexes[0].data) for i in itertools.chain(result)]

    # DOCKER REGISTRY IMPLEMENTATION

    @lru.get
    def get_content(self, path):
        print 20
        path = self._init_path(path)
        logger.debug("get_content %s ", path)
        try:
            return self.data_read(path)
        except Exception:
            raise exceptions.FileNotFoundError("File not found %s" % path)

    @lru.set
    def put_content(self, path, content):
        print 21
        path = self._init_path(path)
        logger.debug("put_content %s %d", path, len(content))
        return self.data_write_file(path, content)

    def stream_write(self, path, fp):
        print 22
        logger.debug("stream_write %s", path)
        first_chunk = True
        while True:
            try:
                path = self._init_path(path)
                buf = fp.read(self.buffer_size)
                if not buf:
                    break

                if not first_chunk:
                    self.data_append(path, buf)
                else:
                    self.data_write_file(path, buf)
                    first_chunk = False

            except IOError as err:
                logger.error("unable to read from a given socket %s", err)
                break

    def stream_read(self, path, bytes_range=None):
        print 23
        logger.debug("read range %s from %s", str(bytes_range), path)
        path = self._init_path(path)
        if not self.exists(path):
            raise exceptions.FileNotFoundError(
                'No such directory: \'{0}\''.format(path))

        if bytes_range is None:
            yield self.s_read(path)
        else:
            offset = bytes_range[0]
            size = bytes_range[1] - bytes_range[0] + 1
            yield self.s_read(path, offset=offset, size=size)

    def list_directory(self, path=None):
        print 24
        path = self._init_path(path)
        logger.debug("list_directory %s ",path)
        if not self.exists(path) and path:
            raise exceptions.FileNotFoundError(
                'No such directory: \'{0}\''.format(path))

        for item in self.s_find(('docker', path)):
            yield item

    def exists(self, path):
        print 25
        path = self._init_path(path)
        logger.debug("Check existance of %s", path)
        try:
            self.data_read(path, 0, 1)
        except exceptions.FileNotFoundError:
            logger.debug("%s doesn't exist", path)
            return False
        else:
            logger.debug("%s exists", path)
            return True

    @lru.remove
    def remove(self, path):
        print 26
        path = self._init_path(path)
        try:
            for item in self.list_directory(path):
                self.s_remove(item)
        except exceptions.FileNotFoundError as err:
            logger.warning(err)
        self.s_remove(path)

    def get_size(self, path):
        print 27
        path = self._init_path(path)
        logger.debug("get_size of %s", path)
        r = self.session.lookup(path)
        r.wait()
        lookups = r.get()
        err = r.error()
        if err.code != 0:
            raise exceptions.FileNotFoundError(
                "Unable to get size of %s %s" % (path, err))
        size = lookups[0].size
        logger.debug("size of %s = %d", path, size)
        return size
