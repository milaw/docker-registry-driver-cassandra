
#docker-registry
from docker_registry.core import driver 
from docker_registry.core import exceptions 
from docker_registry.core import lru

#cassandra
from cassandra.cluster import Cluster
from cassandra.query import dict_factory
from cassandra.query import SimpleStatement
from cassandra.policies import DowngradingConsistencyRetryPolicy
from cassandra.policies import ConstantReconnectionPolicy

DEFAULT_KEYSPACE = "DockerKSpace"
DEFAULT_TABLE_NAME = DEFAULT_KEYSPACE+".DockerImages"
DEFAUL_CLUSTERS_LIST = "127.0.0.1"
DEFAUL_CQL_VERSION = None
DEFAULT_PROTOCOL_VERSION = 2
DEFAULT_PORT = 9042
DEFAULT_COMPRESSION = True
DEFAULT_AUTHENTICATION_PROVIDER = False
DEFAULT_AUTHENTICATION_INFO = ''
DEFAULT_SESSION_TIMEOUT = 10
DEFAULT_SESSION_FETCH_SIZE = 5000

class Storage(driver.Base):

    
    def __init__(self, path=None, config=None):
        # Turn on streaming support
        self.supports_bytes_range = True
        # Increase buffer size up to 640 Kb
        self.buffer_size = 128 * 1024
        # Create default Cassandra config
        self._root_path = config.storage_path or '/'

        
        self._config.clusters_list = (config.cassandra_clusters_list or
                                   DEFAUL_CLUSTERS_LIST)
        # If a specific version of CQL should be used, otherwise, the highest CQL version supported by the server will be automatically used
        self._config.cql_version = (config.cassandra_cql_version or
                                   DEFAUL_CQL_VERSION)
        # The version of the native protocol to use
        self._config.protocol_version = (config.cassandra_protocol_version or
                                    DEFAULT_PROTOCOL_VERSION)
        # The server-side port to open connections to. Defaults to 9042
        self._config.port = (config.cassandra_port or
                                    DEFAULT_PORT)
        #Controls compression for communications between the driver and Cassandra. If left as the default of True
        self._config.compression  = (config.cassandra_compression  or
                                     DEFAULT_COMPRESSION)
        # Authentification
        self._config.authentication_provider =  (config.cassandra_authentication_provider  or
                                     DEFAULT_AUTHENTICATION_PROVIDER)
        self._config.authentication_username  = (config.cassandra_authentication_username or
                                    DEFAULT_AUTHENTICATION_INFO)
        self._config.authentication_password  = (config.cassandra_authentication_password  or
                                    DEFAULT_AUTHENTICATION_INFO)
        # A default timeout, measured in seconds, for queries executed through execute() or execute_async()
        # This timeout currently has no effect on callbacks registered on a ResponseFuture through
        # ResponseFuture.add_callback() or ResponseFuture.add_errback(); even if a query exceeds this default timeout,
        # neither the registered callback or errback will be called.cluster
        self._config.session_timeout = (config.cassandra_session_timeout  or
                                     DEFAULT_SESSION_TIMEOUT)
        # By default, this many rows will be fetched at a time. Setting this to None will disable automatic paging for large query results
        self._config.session_fetch_size  = (config.cassandra_session_fetch_size  or
                                     DEFAULT_SESSION_FETCH_SIZE)

        if self._config.authentication_provider:
            auth_provider = PlainTextAuthProvider(
                username=self._config.authentication_username,password=self._config.authentication_password)
        #The set of IP addresses we pass to the Cluster is simply an initial set of contact points. 
        #After the driver connects to one of these nodes it will automatically discover the rest of 
        #the nodes in the cluster and connect to them, so you don’t need to list every node in your cluster.
        self.cluster = Cluster([clusters_list],
            port=self._config.port,
            protocol_version=self._config.protocol_version,
            auth_provider=auth_provider,
            default_retry_policy=DowngradingConsistencyRetryPolicy(),
            reconnection_policy=ConstantReconnectionPolicy(20.0, 10))
        self.session = self.cluster.connect()
        #CREATE KEYSPACE
        query_ks = "CREATE KEYSPACE IF NOT EXISTS "+ DEFAULT_KEYSPACE +" WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 }; "
        self.session.execute(query_ks)
        #CREATE TABLE
        query_table = "CREATE TABLE IF NOT EXISTS "+ DEFAULT_TABLE_NAME +" (\
                key varchar,\
                value varchar,\
                tag text, \
                PRIMARY KEY (key) \
            ) WITH caching ='keys_only';"
        self.session.execute(query_table)


    def _init_path(self, path=None):
        path = self._root_path + path if path else self._root_path
        return path

    def disconnect_to_cluster():
        cluster.shutdown()


    def data_find(self, tags):
        return 

    def data_remove(self, key):
        fail = False
        query = "DELETE FROM "+ DEFAULT_TABLE_NAME +" WHERE key IN ('"+key+"');"
        rows = self.session.execute(query)
        if fail:
            raise exceptions.FileNotFoundError("No such file %s" % key)

    def data_read(self, path, offset=0, size=0):

        query = "SELECT first_name, last_name FROM "+ DEFAULT_TABLE_NAME +" WHERE empID IN (105, 107, 104);"
        rows = self.session.execute(query)
        return

    def data_write(self, key, value, tags):
        fail = False
        query = "INSERT INTO "+ DEFAULT_TABLE_NAME +" (key,value,tag) VALUES ("+key+","+value+","+tag+") IF NOT EXISTS"
        rows = self.session.execute(query)
        if fail:
            raise exceptions.UnspecifiedError("Indexe setting failed %s" % err)

    def data_append(self, key, content):
        fail = False
        if fail:
            raise exceptions.UnspecifiedError("Writing failed {0}".format(err))

    def data_write_file(self, path, content):
        return 

    def data_find(self, tags):
        r = self._session.find_all_indexes(list(tags))
        r.wait()
        result = r.get()
        return [str(i.indexes[0].data) for i in itertools.chain(result)]

    
    #DOCKER REGISTRY IMPLEMENTATION

    @lru.get
    def get_content(self, path):
        path = self._init_path(path)
        try:
            return self.data_read(path)
        except Exception:
            raise exceptions.FileNotFoundError("File not found %s" % path)

    @lru.set
    def put_content(self, path, content):
        path = self._init_path(path)
        logger.debug("put_content %s %d", path, len(content))
        return self.data_write_file(path, content)

    def stream_write(self, path, fp):
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
        path = self._init_path(path)
        if not self.exists(path) and path:
            raise exceptions.FileNotFoundError(
                'No such directory: \'{0}\''.format(path))

        for item in self.s_find(('docker', path)):
            yield item

    def exists(self, path):
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
        path = self._init_path(path)
        try:
            for item in self.list_directory(path):
                self.s_remove(item)
        except exceptions.FileNotFoundError as err:
            logger.warning(err)
        self.s_remove(path)

    def get_size(self, path):
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

