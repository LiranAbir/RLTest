import shutil
import tempfile
from unittest import TestCase
from unittest.mock import patch

from RLTest import Env
from RLTest.redis_cluster import ClusterEnv
from tests.unit.test_common import REDIS_BINARY


class TestEnvOss(TestCase):

    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.env = None

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cluster_bus_setting_forwarding_and_comparison(self):
        # Inspect constructed runners without starting servers: True would
        # require TLS on Redis builds that implement the option.
        with patch.object(Env, 'start'), patch('RLTest.redis_std.StandardEnv._getRedisVersion', return_value=(8, 11, 224)):
            envs = [Env(env='oss-cluster', shardsCount=3, logDir=self.test_dir,
                        redisBinaryPath=REDIS_BINARY, clusterBusProtectedMode=value)
                    for value in (None, False, True)]
            for value, env in zip((None, False, True), envs):
                assert env.clusterBusProtectedMode is value
                assert all(shard.clusterBusProtectedMode is value for shard in env.envRunner.shards)
            assert not envs[0].compareEnvs(envs[1])
            assert not envs[1].compareEnvs(envs[2])
            assert envs[1].getEnvKwargs()['clusterBusProtectedMode'] is False

    def test_compare_envs(self):
        pass

    def test_get_env_by_name(self):
        self.env = Env(useSlaves=False, env='oss', logDir=self.test_dir, redisBinaryPath=REDIS_BINARY)
        assert self.env.isUp() == True
        self.env.stop()
        assert self.env.isUp() == False

    def test_start(self):
        pass

    def test_stop(self):
        pass

    def test_get_env_str(self):
        self.env = Env(useSlaves=True, env='oss', logDir=self.test_dir, redisBinaryPath=REDIS_BINARY)
        assert self.env.getEnvStr() == 'oss'
        self.env.stop()
        assert self.env.isUp() == False

    def test_compare_env(self):
        self.env = Env(env='oss', logDir=self.test_dir, redisBinaryPath=REDIS_BINARY)
        env = Env(env='oss', logDir=self.test_dir, redisBinaryPath=REDIS_BINARY)
        assert self.env.compareEnvs(env) is True
        env.stop()
        env = Env(env='oss', logDir=self.test_dir, redisBinaryPath=REDIS_BINARY, useAof=True)
        assert self.env.compareEnvs(env) is False
        env.stop()
        self.env.stop()

    def test_get_connection(self):
        pass

    def test_get_slave_connection(self):
        pass

    def test_get_master_nodes_list(self):
        pass

    def test_get_ossmaster_nodes_connection_list(self):
        pass

    def test_flush(self):
        pass

    def test_is_cluster(self):
        self.env = Env(useSlaves=True, env='oss', logDir=self.test_dir, redisBinaryPath=REDIS_BINARY)
        assert self.env.isCluster() == False
        assert self.env.isUp() == True
        self.env.stop()
        assert self.env.isUp() == False
        self.env = Env(useSlaves=True, env='oss-cluster', logDir=self.test_dir, redisBinaryPath=REDIS_BINARY)
        assert self.env.isCluster() == True
        self.env.stop()

    def test_is_enterpise_cluster(self):
        pass

    def test_is_debugger(self):
        pass

    def test__get_caller_position(self):
        pass

    def test__assertion(self):
        pass

    def test_get_number_of_failed_assertion(self):
        pass

    def test_assert_equal(self):
        pass

    def test_assert_not_equal(self):
        pass

    def test_assert_ok(self):
        pass

    def test_assert_true(self):
        pass

    def test_assert_false(self):
        pass

    def test_assert_contains(self):
        pass

    def test_assert_not_contains(self):
        pass

    def test_assert_greater_equal(self):
        pass

    def test_assert_greater(self):
        pass

    def test_assert_less_equal(self):
        pass

    def test_assert_less(self):
        pass

    def test_assert_is_not_none(self):
        pass

    def test_assert_is_none(self):
        pass

    def test_assert_is_instance(self):
        pass

    def test_assert_almost_equal(self):
        pass

    def test_expect(self):
        pass

    def test_cmd(self):
        pass

    def test_assert_cmd_ok(self):
        pass

    def test_exists(self):
        pass

    def test_assert_exists(self):
        pass

    def test_execute_command(self):
        pass

    def test_reloading_iterator(self):
        pass

    def test_dump_and_reload(self):
        pass

    def test_hmset(self):
        pass

    def test_keys(self):
        pass

    def test_assert_raises(self):
        pass

    def test_assert_response_error(self):
        pass

    def test_restart_and_reload(self):
        pass

    def test_broadcast(self):
        pass

    def test_debug_print(self):
        pass

    def test_check_exit_code(self):
        pass

    def test_is_up(self):
        self.env = Env(useSlaves=True, env='oss', logDir=self.test_dir, redisBinaryPath=REDIS_BINARY)
        assert self.env.isCluster() == False
        assert self.env.isUp() == True
        self.env.stop()
        assert self.env.isUp() == False

    def test_skip(self):
        pass

    def test_skip_on_debugger(self):
        pass

    def test_skip_on_cluster(self):
        pass

    def test_is_unix_socket(self):
        self.env = Env(useSlaves=True, env='oss', logDir=self.test_dir, redisBinaryPath=REDIS_BINARY)
        assert self.env.isCluster() == False
        assert self.env.isUp() == True
        assert self.env.isUnixSocket() == False
        self.env.stop()
        assert self.env.isUp() == False

    def test_is_tcp(self):
        self.env = Env(useSlaves=True, env='oss', logDir=self.test_dir, redisBinaryPath=REDIS_BINARY)
        assert self.env.isCluster() == False
        assert self.env.isUp() == True
        assert self.env.isTcp() == True
        self.env.stop()
        assert self.env.isUp() == False

    def test_skip_on_tcp(self):
        pass

    def test_skip_on_unix_socket(self):
        pass

    def test_skip_on_enterprise_cluster(self):
        pass

    def test_with_password(self):
        password = 'GoodPassword42'
        self.env = Env(useSlaves=True, env='oss', password=password, logDir=self.test_dir, redisBinaryPath=REDIS_BINARY)
        assert self.env.envRunner.getPassword() == password
        conn = self.env.getConnection()
        assert conn.ping() == True
        self.env.stop()
        assert self.env.isUp() == False
        self.env = Env(useSlaves=True, env='oss-cluster', password=password, logDir=self.test_dir, redisBinaryPath=REDIS_BINARY)
        assert isinstance(self.env.envRunner, ClusterEnv)
        assert self.env.envRunner.password == password
        conn = self.env.getConnection()
        assert conn.ping() == True
        self.env.stop()
        assert self.env.isUp() == False
