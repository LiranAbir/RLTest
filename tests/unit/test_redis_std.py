import os
import shutil
import tempfile
from unittest import TestCase

from RLTest.redis_std import MASTER, StandardEnv, hasClusterBusProtectedMode
from tests.unit.test_common import REDIS_BINARY, TLS_CERT, TLS_KEY, TLS_CACERT

tlsCertFile = 'fake_redis.crt'
tlsKeyFile = 'fake_redis.key'
tlsCaCertFile = 'fake_ca.crt'


class TestStandardEnv(TestCase):

    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        # Create a file in the temporary directory
        with open(os.path.join(self.test_dir, tlsCertFile), 'w') as f:
            f.write('tlsCertFile')
        with open(os.path.join(self.test_dir, tlsKeyFile), 'w') as f:
            f.write('tlsKeyFile')
        with open(os.path.join(self.test_dir, tlsCaCertFile), 'w') as f:
            f.write('tlsCaCertFile')

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def test__get_file_name(self):
        pass

    def test__get_valgrind_file_path(self):
        pass

    def test_get_master_port(self):
        std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir)
        assert std_env.getMasterPort() == 6379
        env2 = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir,
                           port=10000)
        assert env2.getMasterPort() == 10000
        pass

    def test_get_password(self):
        std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir)
        assert std_env.getPassword() == None
        std_env_pass = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir,
                                   password="passwd")
        assert std_env_pass.getPassword() == "passwd"

    def test_get_unix_path(self):
        pass

    def test_get_tlscert_file(self):
        if not os.path.isfile(TLS_CERT) or not os.path.isfile(TLS_KEY) or not os.path.isfile(TLS_CACERT):
            self.skipTest("missing required tls files")
        tls_std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', useTLS=True,
                                  tlsCertFile=os.path.join(self.test_dir, tlsCertFile),
                                  tlsKeyFile=os.path.join(self.test_dir, tlsKeyFile),
                                  tlsCaCertFile=os.path.join(self.test_dir, tlsCaCertFile), port=8000)
        assert os.path.join(self.test_dir, tlsCertFile) == tls_std_env.getTLSCertFile()

    def test_get_tlskey_file(self):
        if not os.path.isfile(TLS_CERT) or not os.path.isfile(TLS_KEY) or not os.path.isfile(TLS_CACERT):
            self.skipTest("missing required tls files")
        tls_std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', useTLS=True,
                                  tlsCertFile=os.path.join(self.test_dir, tlsCertFile),
                                  tlsKeyFile=os.path.join(self.test_dir, tlsKeyFile),
                                  tlsCaCertFile=os.path.join(self.test_dir, tlsCaCertFile), port=8000)
        assert os.path.join(self.test_dir, tlsKeyFile) == tls_std_env.getTLSKeyFile()

    def test_get_tlscacert_file(self):
        if not os.path.isfile(TLS_CERT) or not os.path.isfile(TLS_KEY) or not os.path.isfile(TLS_CACERT):
            self.skipTest("missing required tls files")
        tls_std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', useTLS=True,
                                  tlsCertFile=os.path.join(self.test_dir, tlsCertFile),
                                  tlsKeyFile=os.path.join(self.test_dir, tlsKeyFile),
                                  tlsCaCertFile=os.path.join(self.test_dir, tlsCaCertFile), port=8000)
        assert os.path.join(self.test_dir, tlsCaCertFile) == tls_std_env.getTLSCACertFile()

    def test_has_interactive_debugger(self):
        std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test')
        assert std_env.has_interactive_debugger == None

    def _fakeRedisBinary(self, name, startupOutput, version='8.8.0'):
        """A stand-in redis that reports `version` and prints `startupOutput`.

        Lets the probe be tested against a binary whose version and whose actual
        support for the option disagree, which is the case version numbers
        cannot get right.
        """
        path = os.path.join(self.test_dir, name)
        with open(path, 'w') as f:
            f.write('#!/bin/sh\n'
                    'case "$1" in --version) echo "Redis server v=%s sha=00000000:0 bits=64"; exit 0;; esac\n'
                    'echo "%s"\n'
                    'exit 1\n' % (version, startupOutput))
        os.chmod(path, 0o755)
        return path

    def test_has_cluster_bus_protected_mode_probes_the_binary(self):
        unsupported = self._fakeRedisBinary('redis-unsupported',
                                            'Bad directive or wrong number of arguments')
        supported = self._fakeRedisBinary('redis-supported',
                                          'Configured to not listen anywhere, exiting.')
        assert not hasClusterBusProtectedMode(unsupported)
        assert hasClusterBusProtectedMode(supported)
        # Answer is cached, so removing the binary changes nothing.
        os.remove(unsupported)
        assert not hasClusterBusProtectedMode(unsupported)

    def test_create_cmd_args_cluster_bus_protected_mode(self):
        flag = ['--cluster-bus-port-protected-mode', 'no']

        def args(binary, **kwargs):
            env = StandardEnv(redisBinaryPath=binary, outputFilesFormat='%s-test',
                              dbDirPath=self.test_dir, **kwargs)
            return env.createCmdArgs(MASTER)

        # The option was added mid-release-line and backported, so a version
        # number cannot say whether a given build has it: 8.8.0 through 8.8.2 do
        # not, 8.8.3 does, and the same holds for 8.10.1 versus 8.10.2. Passing
        # it to a build without it is fatal, so these must not be waived blind.
        for version in ('8.8.0', '8.8.2', '8.10.1', '255.255.255'):
            binary = self._fakeRedisBinary('redis-no-option-' + version,
                                           'Bad directive or wrong number of arguments', version)
            assert flag[0] not in args(binary, clusterEnabled=True), version

        for version in ('8.8.3', '8.10.2', '255.255.255'):
            binary = self._fakeRedisBinary('redis-with-option-' + version,
                                           'Configured to not listen anywhere, exiting.', version)
            cmdArgs = args(binary, clusterEnabled=True)
            assert cmdArgs[-2:] == flag, (version, cmdArgs)

        supported = self._fakeRedisBinary('redis-plain',
                                          'Configured to not listen anywhere, exiting.')
        # Only a cluster node opens a bus port, and tls-cluster authenticates it.
        assert flag[0] not in args(supported)
        tlsArgs = args(supported, clusterEnabled=True, useTLS=True,
                       tlsCertFile=os.path.join(self.test_dir, tlsCertFile),
                       tlsKeyFile=os.path.join(self.test_dir, tlsKeyFile),
                       tlsCaCertFile=os.path.join(self.test_dir, tlsCaCertFile))
        assert flag[0] not in tlsArgs
        assert '--tls-cluster' in tlsArgs

    def test_create_cmd_args_default(self):
        std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test')
        role = 'master'
        cmd_args = std_env.createCmdArgs(role)
        assert [REDIS_BINARY, '--port', '6379', '--logfile', std_env._getFileName(role, '.log'), '--dbfilename',
                std_env._getFileName(role, '.rdb')] == cmd_args
    
    def test_create_cmd_args_config_file(self):
        std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test',
                              redisConfigFile='redis.conf')
        role = 'master'
        cmd_args = std_env.createCmdArgs(role)
        assert [REDIS_BINARY, 'redis.conf','--port', '6379', '--logfile', std_env._getFileName(role, '.log'), '--dbfilename',
                std_env._getFileName(role, '.rdb')] == cmd_args

    def test_create_cmd_args_tls(self):
        port = 8000
        tls_std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', useTLS=True,
                                  tlsCertFile=os.path.join(self.test_dir, tlsCertFile),
                                  tlsKeyFile=os.path.join(self.test_dir, tlsKeyFile),
                                  tlsCaCertFile=os.path.join(self.test_dir, tlsCaCertFile), port=8000)
        role = 'master'
        cmd_args = tls_std_env.createCmdArgs(role)
        assert [REDIS_BINARY, '--port', '0', '--tls-port', '{}'.format(port), '--logfile',
                tls_std_env._getFileName(role, '.log'), '--dbfilename',
                tls_std_env._getFileName(role, '.rdb'), '--tls-cert-file', os.path.join(self.test_dir, tlsCertFile),
                '--tls-key-file', os.path.join(self.test_dir, tlsKeyFile), '--tls-ca-cert-file',
                os.path.join(self.test_dir, tlsCaCertFile), '--tls-replication', 'yes'] == cmd_args

    def test_create_cmd_args_modules_default_behaviour(self):
        port = 8000
        temp = tempfile.TemporaryFile()
        directory_name = tempfile.mkdtemp()
        temp_file = tempfile.NamedTemporaryFile(dir=directory_name)
        module_std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test',
                                     port=port, modulePath=temp_file.name, moduleArgs="P1 V1 P2 V2")
        role = 'master'
        cmd_args = module_std_env.createCmdArgs(role)
        assert [REDIS_BINARY, '--port', '{}'.format(port),
                '--loadmodule', temp_file.name, 'P1', 'V1', 'P2', 'V2',
                '--logfile',  module_std_env._getFileName(role, '.log'),
                '--dbfilename', module_std_env._getFileName(role, '.rdb')] == cmd_args
        shutil.rmtree(directory_name)

    def test_create_cmd_args_modules_one_module_array(self):
        port = 8000
        temp = tempfile.TemporaryFile()
        directory_name = tempfile.mkdtemp()
        temp_file = tempfile.NamedTemporaryFile(dir=directory_name)
        module_std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test',
                                     port=port, modulePath=[temp_file.name], moduleArgs=["P1 V1 P2 V2"])
        role = 'master'
        cmd_args = module_std_env.createCmdArgs(role)
        assert [REDIS_BINARY, '--port', '{}'.format(port),
                '--loadmodule', temp_file.name, 'P1', 'V1', 'P2', 'V2',
                '--logfile',  module_std_env._getFileName(role, '.log'),
                '--dbfilename', module_std_env._getFileName(role, '.rdb')] == cmd_args
        shutil.rmtree(directory_name)

    def test_create_cmd_args_modules_two_modules_array(self):
        port = 8000
        temp = tempfile.TemporaryFile()
        directory_name = tempfile.mkdtemp()
        temp_file1 = tempfile.NamedTemporaryFile(dir=directory_name)
        temp_file2 = tempfile.NamedTemporaryFile(dir=directory_name)
        module_std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test',
                                     port=port, modulePath=[temp_file1.name, temp_file2.name], moduleArgs=["P1 V1 P2 V2", ""])
        role = 'master'
        cmd_args = module_std_env.createCmdArgs(role)
        assert [REDIS_BINARY, '--port', '{}'.format(port),
                '--loadmodule', temp_file1.name, 'P1', 'V1', 'P2', 'V2',
                '--loadmodule', temp_file2.name,
                '--logfile', module_std_env._getFileName(role, '.log'),
                '--dbfilename', module_std_env._getFileName(role, '.rdb')] == cmd_args
        shutil.rmtree(directory_name)

    def test_create_cmd_args_aof_without_rdb_preamble(self):
        port = 8000
        aof_std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test',
                                  useAof=True, useRdbPreamble=False, port=8000)
        role = 'master'
        cmd_args = aof_std_env.createCmdArgs(role)
        assert [REDIS_BINARY, '--port', '{}'.format(port), '--logfile',
                aof_std_env._getFileName(role, '.log'), '--dbfilename',
                aof_std_env._getFileName(role, '.rdb'), '--appendonly', 'yes',
                '--appendfilename', aof_std_env._getFileName(role, '.aof'),
                '--aof-use-rdb-preamble', 'no'] == cmd_args

    def test_wait_for_redis_to_start(self):
        pass

    def test_get_pid(self):
        pass

    def test_get_port(self):
        std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir)
        assert std_env.getPort('master') == 6379
        std_env_slave = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir,
                                    useSlaves=True)
        assert std_env_slave.getPort('slave') == 6380
        env2 = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir,
                           port=10000)
        assert env2.getPort('master') == 10000

        env2_slave = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir,
                                 useSlaves=True, port=10000)
        assert env2_slave.getPort('slave') == 10001

    def test_get_server_id(self):
        std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir)
        assert std_env.getServerId('master') == 1
        std_env_id2 = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir,
                                  serverId=2)
        assert std_env_id2.getServerId('master') == 2

    def test__print_env_data(self):
        pass

    def test_print_env_data(self):
        pass

    def test__is_alive(self):
        std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir)
        assert std_env.isUp() == False
        std_env.startEnv()
        assert std_env._isAlive(std_env.masterProcess) == True
        std_env.stopEnv()
        assert std_env._isAlive(std_env.masterProcess) == False

    def test__stop_process(self):
        std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir, useSlaves=True)
        assert std_env.isUp() == False
        std_env.startEnv()
        assert std_env._isAlive(std_env.masterProcess) == True
        assert std_env._isAlive(std_env.slaveProcess) == True
        std_env.stopEnv()
        assert std_env._isAlive(std_env.masterProcess) == False
        assert std_env._isAlive(std_env.slaveProcess) == False

        std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir, useSlaves=True)
        assert std_env.isUp() == False
        std_env.startEnv()
        assert std_env._isAlive(std_env.masterProcess) == True
        assert std_env._isAlive(std_env.slaveProcess) == True
        assert std_env.isUp() == True
        assert  std_env.isHealthy() == True
        std_env.stopEnv(masters=True, slaves=False)
        assert std_env._isAlive(std_env.masterProcess) == False
        assert std_env._isAlive(std_env.slaveProcess) == True
        assert std_env.isUp() == True
        assert std_env.isHealthy() == False
        std_env.stopEnv(slaves=True)
        assert std_env._isAlive(std_env.masterProcess) == False
        assert std_env._isAlive(std_env.slaveProcess) == False
        assert std_env.isUp() == False
        assert std_env.isHealthy() == False

    def test__start_process(self):
        std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir,
                              useSlaves=True)
        assert std_env.isUp() == False
        std_env.startEnv()
        assert std_env._isAlive(std_env.masterProcess) == True
        assert std_env._isAlive(std_env.slaveProcess) == True
        std_env.stopEnv()
        assert std_env._isAlive(std_env.masterProcess) == False
        assert std_env._isAlive(std_env.slaveProcess) == False
        assert std_env.isUp() == False
        assert std_env.isHealthy() == False

        std_env.startEnv(masters=True, slaves=False)
        assert std_env._isAlive(std_env.masterProcess) == True
        assert std_env._isAlive(std_env.slaveProcess) == False
        assert std_env.isUp() == True
        assert std_env.isHealthy() == False

        std_env.stopEnv()
        assert std_env._isAlive(std_env.masterProcess) == False
        assert std_env._isAlive(std_env.slaveProcess) == False
        assert std_env.isUp() == False
        assert std_env.isHealthy() == False

        std_env.startEnv(masters=False, slaves=True)
        assert std_env._isAlive(std_env.masterProcess) == False
        assert std_env._isAlive(std_env.slaveProcess) == True
        assert std_env.isUp() == True
        assert std_env.isHealthy() == False

        std_env.stopEnv()
        assert std_env._isAlive(std_env.masterProcess) == False
        assert std_env._isAlive(std_env.slaveProcess) == False
        assert std_env.isUp() == False
        assert std_env.isHealthy() == False

        std_env.startEnv()
        assert std_env._isAlive(std_env.masterProcess) == True
        assert std_env._isAlive(std_env.slaveProcess) == True
        assert std_env.isUp() == True
        assert std_env.isHealthy() == True

        std_env.stopEnv(masters=True, slaves=False)
        assert std_env._isAlive(std_env.masterProcess) == False
        assert std_env._isAlive(std_env.slaveProcess) == True
        assert std_env.isUp() == True
        assert std_env.isHealthy() == False

        std_env.startEnv()
        assert std_env._isAlive(std_env.masterProcess) == True
        assert std_env._isAlive(std_env.slaveProcess) == True
        assert std_env.isUp() == True
        assert std_env.isHealthy() == True

        std_env.stopEnv(masters=False, slaves=True)
        assert std_env._isAlive(std_env.masterProcess) == True
        assert std_env._isAlive(std_env.slaveProcess) == False
        assert std_env.isUp() == True
        assert std_env.isHealthy() == False

        std_env.startEnv()
        assert std_env._isAlive(std_env.masterProcess) == True
        assert std_env._isAlive(std_env.slaveProcess) == True
        assert std_env.isUp() == True
        assert std_env.isHealthy() == True

        std_env.stopEnv()



    def test_verbose_analyse_server_log(self):
        pass

    def test__get_connection(self):
        pass

    def test_get_connection(self):
        pass

    def test_get_ossmaster_nodes_connection_list(self):
        pass

    def test_get_slave_connection(self):
        pass

    def test_get_master_nodes_list(self):
        pass

    def test_flush(self):
        pass

    def test__wait_for_child(self):
        pass

    def test_dump_and_reload(self):
        pass

    def test_broadcast(self):
        pass

    def test_check_exit_code(self):
        pass

    def test_is_up(self):
        std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir)
        assert std_env.isUp() == False
        std_env.startEnv()
        assert std_env.isUp() == True
        std_env.stopEnv()
        assert std_env.isUp() == False

    def test_is_unix_socket(self):
        std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir)
        assert std_env.isUnixSocket() == False

    def test_is_tcp(self):
        std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir)
        assert std_env.isTcp() == True

    def test_is_tls(self):
        std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir)
        std_env.startEnv()
        assert std_env.isTLS() == False
        std_env.stopEnv()
        if not os.path.isfile(TLS_CERT) or not os.path.isfile(TLS_KEY) or not os.path.isfile(TLS_CACERT):
            self.skipTest("missing required tls files")

        tls_std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir,
                                  useTLS=True,
                                  tlsCertFile=TLS_CERT,
                                  tlsKeyFile=TLS_KEY,
                                  tlsCaCertFile=TLS_CACERT)
        tls_std_env.startEnv()
        assert tls_std_env.isTLS() == True
        tls_std_env.stopEnv()

    def test_exists(self):
        pass

    def test_hmset(self):
        pass

    def test_keys(self):
        pass

    def test_get_connection_by_key(self):
        tagsCount = 3
        std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir)
        std_env.startEnv()
        for i in range(tagsCount):
            key = 'x{%i}' % i
            con = std_env.getConnectionByKey(key, "set")
            assert(con.set(key, "1"))
        std_env.stopEnv()

    def test_cluster_node_timeout(self):
        std_env = StandardEnv(redisBinaryPath=REDIS_BINARY, outputFilesFormat='%s-test', dbDirPath=self.test_dir, clusterNodeTimeout=60000)
        std_env.startEnv()
        con = std_env.getConnection()
        assert(con.execute_command("CONFIG", "GET", "cluster-node-timeout"), "60000")
        std_env.stopEnv()
