# to import cassandra from global namespace
# instead of local directory
from __future__ import absolute_import

import itertools
import logging
import time
import sys
import json
import os

# cassandra
from cassandra.cluster import Cluster
from cassandra.query import dict_factory
from cassandra.query import SimpleStatement
from cassandra.query import ValueSequence
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
        print "__init__--------------------------------------------------"
        # Turn on streaming support
        self.supports_bytes_range = True
        # Increase buffer size up to 640 Kb
        self.buffer_size = 128 * 1024
        # Create default Cassandra config
        self._root_path = '/'
        if not self._root_path.endswith('/'):
            self._root_path += '/'

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


    def create_schema(self):
        print "__init__--------------------------------------------------"
         # CREATE KEYSPACE
        self.session.execute("""
            CREATE KEYSPACE IF NOT EXISTS DockerKSpace
            WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 };
        """)
        logger.debug("KEYSPACE executed!")
        
        # CREATE TABLES
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS DockerKSpace.DockerRepositories (
                key varchar,
                type varchar,
                value varchar,
                PRIMARY KEY (key) 
            ) WITH caching ='keys_only';
        """)
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS DockerKSpace.DockerImages (
                key varchar,
                imageid varchar,
                value varchar,
                image blob,
                size bigint,               
                PRIMARY KEY (key) 
            ) WITH caching ='keys_only';
        """)
        logger.debug("TABLE executed!")
        self.session.execute("""
            CREATE INDEX IF NOT EXISTS index_type ON DockerKSpace.DockerRepositories (type);
        """)
        logger.debug("INDEX executed!")


    def _init_path(self, path=None, create=False):
        path = path if path else self._root_path
        if create is True:
            dirname = os.path.dirname(path)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
        return path

    def get_image_id(self, path):
        s_path = path.split("/")
        imageid = s_path[len(s_path)-2]
        return imageid

    def get_state(self, path):
        s_path = path.split("/")
        state = s_path[len(s_path)-1]
        return state

    def disconnect_to_cluster(self):
        self.cluster.shutdown()
        self.session.shutdown()
        logger.info('Connection closed')


    def data_read(self, path, offset=0, size=0):
        print "data_read--------------------------------------------------"
        print path
        if "repositories" in path:
            print "repositories inside"
            results = self.session.execute(\
                "SELECT value FROM DockerKSpace.DockerRepositories WHERE key = %s LIMIT 1", (path, ))
        else:
            print "images inside"
            results = self.session.execute(\
                "SELECT value FROM DockerKSpace.DockerImages WHERE key = %s LIMIT 1", (path, ))

        if not results:
            print "throw execption for not found"
            raise exceptions.FileNotFoundError("File not found %s" % path)
        else:
            print 'create data_str'
            data_str=str(results[0].value)
        return data_str


    def data_write_content(self, path, content):
        print "data_write_content--------------------------------------------------"
        state = self.get_state(path)
        print path
        logger.debug("put_content: write %s with content %s and state %s", path, content, state)
        if "repositories" in path:
            print "repositories inside"
            results = self.session.execute("INSERT INTO DockerKSpace.DockerRepositories (key, type, value) VALUES (%s, %s, %s)", (path, 'FILE', content))
            s_path = os.path.split(path)
            dir_path = s_path[0]
            self.session.execute("INSERT INTO DockerKSpace.DockerRepositories (key, type) VALUES (%s, %s) IF NOT EXISTS", (dir_path, 'DIRECTORY'))

        else:
            imageid = self.get_image_id(path)
            print "images inside"
            results = self.session.execute("INSERT INTO DockerKSpace.DockerImages (key, imageid, value) VALUES (%s, %s, %s)", (path, imageid, content))


    # -------------------------------------------------------------------------
    # DOCKER REGISTRY IMPLEMENTATION
    # -------------------------------------------------------------------------
    @lru.get
    def get_content(self, path):
        print "get_content--------------------------------------------------"
        path = self._init_path(path)
        logger.debug("path to read : %s", path)
        return self.data_read(path)


    @lru.set
    def put_content(self, path, content):
        print "put_content--------------------------------------------------"
        results = self.data_write_content(path, content)
        return path


    def exists(self, path):
        print "exists--------------------------------------------------"
        try:
            self.data_read(path)
        except exceptions.FileNotFoundError:
            logger.debug("%s doesn't exist", path)
            return False
        else:
            logger.debug("%s exists", path)
        return True


    def stream_write(self, path, fp):
        print "stream_write--------------------------------------------------"
        path = self._init_path(path, create=True)
        logger.debug("path to read : %s", path)
        self.insert_statement = self.session.prepare("""
            INSERT INTO DockerKSpace.DockerImages (key, imageid, image)
            VALUES (?, ?, ?);
        """)
        imageid = self.get_image_id(path)
        with open(path, mode='wb') as f:
            try:
                while True:
                    buf = fp.read(self.buffer_size)
                    if not buf:
                        break
                    else:
                        #self.session.execute(insert_statement.bind((path, imageid, buf)))
                        self.session.execute(self.insert_statement,[path, imageid, buf])
                        f.write(buf)

                msize = os.path.getsize(path)
                print path
                print msize
                self.session.execute("UPDATE DockerKSpace.DockerImages SET size=%s WHERE key=%s", (msize, path))
                #if os.path.isfile(path):
                #    os.remove(path)
                #dirname = os.path.dirname(path)
                #if os.path.exists(dirname):
                #    os.rmdir(dirname)

            except IOError as err:
                logger.error("unable to read from a given socket %s", err)
                pass


    @lru.remove
    def remove(self, path):
        print "remove--------------------------------------------------"
        state = self.get_state(path)
        if state is "_inprogress":
            s_path = os.path.split(path)
            path = s_path[0]
            logger.debug("path to remove : %s", path)
        try:
            if "repositories" in path:
                results = self.session.execute(\
                    "DELETE FROM DockerKSpace.DockerRepositories WHERE key = %s", (path, ))
            else:
                results = self.session.execute(\
                    "DELETE FROM DockerKSpace.DockerImages WHERE key = %s", (path, ))
    
        except OSError:
            raise exceptions.FileNotFoundError('%s is not there' % path)


    def list_directory(self, path=None):
        print "list_directory--------------------------------------------------"
        logger.debug("list_directory %s ",path)
        if not self.exists(path) and path:
            raise exceptions.FileNotFoundError(
                'No such key: \'{0}\''.format(path))

        if "repositories" in path:
            print "repositories inside"
            results = self.session.execute(\
                "SELECT key FROM DockerKSpace.DockerRepositories WHERE type = %s", ('FILE', ))
        else:
            print "images inside"
            results = self.session.execute(\
                "SELECT value FROM DockerKSpace.DockerImages WHERE key = %s LIMIT 1", (path, ))
        print results

        for item in results:
            print item
            yield item.key


    def stream_read(self, path, bytes_range=None):
        print "stream_read--------------------------------------------------"
        logger.debug("read range %s from %s", str(bytes_range), path)
        if not self.exists(path):
            raise exceptions.FileNotFoundError(
                'No such directory: \'{0}\''.format(path))

        if bytes_range is None:
            yield self.data_read(path)
        else:
            offset = bytes_range[0]
            size = bytes_range[1] - bytes_range[0] + 1
            yield self.data_read(path, offset=offset, size=size)

    #TODO --- SELECT FROM IMAGES SIZE value
    def get_size(self, path):
        print "get_size--------------------------------------------------"
        #path = self._init_path(path)
        print "get_size of %s" % path
        try:
            if "images" in path:
                print "images inside"
                results = self.session.execute(\
                    "SELECT size FROM DockerKSpace.DockerImages WHERE key = %s LIMIT 1", (path, ))
            print results

        except OSError:
            raise exceptions.FileNotFoundError(
                "Unable to get size of %s %s" % (path, err))
        
        logger.debug("size of %s = %d", path, results[0].size)
        return results[0].size
