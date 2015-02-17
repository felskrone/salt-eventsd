import time
from mock import patch
from salt.utils.event import SaltEvent
from salteventsd.daemon import SaltEventsDaemon
from salteventsd.loader import SaltEventsdLoader


def main():
    with patch.object(SaltEvent, 'get_event', autospec=True) as m:
        with patch.object(SaltEvent, '__init__', autospec=True) as s:
            with patch.object(SaltEventsdLoader, '_read_yaml', autospec=True) as t:
                def mock_getopts(self, *args, **kwargs):
                    self.opts = {
                        'worker_credentials': {
                            'all': {
                                'salt-master': 'localhost'
                            }
                        },
                        'events': {
                            'benchmark': {
                                'dict_name': 'data',
                                'template': "insert into {0} (jid, srv_id, retcode, returns, success) values ('{1}', '{2}', '{3}', '{4}', '{5}');",
                                'debug': True,
                                'fields': ['jid', 'id', 'retcode', 'return', 'success'],
                                'backend': 'Bench_Worker',
                                'tag': 'salt/job/[0-9]*/ret/\\w+',
                                'mysql_tab': 'returns'
                            }
                        },
                        'general': {
                            'backend_dir': '/etc/salt/eventsd_workers',
                            'backends': ['Bench_Worker'],
                            'dump_timer': 1,
                            'event_limit': 200,
                            'id': 'master',
                            'logfile': '/var/log/salt/eventsd',
                            'loglevel': 'debug',
                            'max_workers': 20,
                            'node': 'master',
                            'pidfile': '/var/run/salt-eventsd.pid',
                            'sock_dir': '/var/run/salt/master',
                            'state_file': '/var/run/salt-eventsd.status',
                            'state_timer': 25
                        }
                    }

                def mock_init(self, *args, **kwargs):
                    self.puburi = "MOCK self.puburi"

                def side_effect(self, *args, **kwargs):
                    time.sleep(0.0005)  # 2000 e/sec  : Real throughput ~1200 events/sec with empty worker
                    # time.sleep(0.001)  # 1000 e/sec  : Real throughput ~700 events/sec with empty worker
                    # time.sleep(0.002)  # 500 e/sec : Real throughput ~400 events/sec with empty worker

                    self.counter += 1

                    return {
                        'tag': 'salt/job/20150125205220169454/ret/Graken',
                        'data': {
                            'fun_args': [],
                            'jid': '20150125205220169454',
                            'return': True,
                            'retcode': 0,
                            'success': True,
                            'cmd': '_return',
                            '_stamp': '2015-01-25T20:52:20.291129',
                            'fun': 'test.ping',
                            'id': 'Graken'
                        }
                    }

                t.side_effect = mock_getopts
                s.side_effect = mock_init
                m.side_effect = side_effect

                daemon = SaltEventsDaemon(
                    config="/etc/salt/eventsd",
                    log_level="info",
                    log_file="/tmp/salt-eventsd-benchmark.log",
                    daemonize=False,
                )

                daemon.event_limit = 100
                daemon.listen()


if __name__ == '__main__':
    main()
