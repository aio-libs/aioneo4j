import socket
import time
import uuid

import pytest
from docker import from_env as docker_from_env

from aioneo4j import Neo4j


@pytest.fixture(scope='session')
def session_id():
    '''Unique session identifier, random string.'''
    return str(uuid.uuid4())


@pytest.fixture(scope='session')
def docker():
    client = docker_from_env(version='auto')
    return client


def pytest_addoption(parser):
    parser.addoption("--neo4j_tag", action="append", default=[],
                     help=("Neo4j server versions, e.g. 2.3 or 3.0 "
                           "May be used several times. "))


def pytest_generate_tests(metafunc):
    if 'neo4j_tag' in metafunc.fixturenames:
        tags = set(metafunc.config.option.neo4j_tag)
        if not tags:
            tags = ['latest']
        else:
            tags = list(tags)
        metafunc.parametrize("neo4j_tag", tags, scope='session')


@pytest.fixture(scope='session')
def neo4j_server(docker, session_id, neo4j_tag, tmpdir_factory, request):
    data_dir = tmpdir_factory.mktemp('neo4j-db-'+session_id, numbered=True)
    logs_dir = tmpdir_factory.mktemp('neo4j-logs-'+session_id, numbered=True)

    container = docker.containers.run(
        image='neo4j:{}'.format(neo4j_tag),
        name='aioneo4j-test-server-{}-{}'.format(neo4j_tag, session_id),
        ports={'7474/tcp': None,
               '7473/tcp': None,
               '7687/tcp': None},
        volumes={data_dir: {'bind': '/data', 'mode': 'rw'},
                 logs_dir: {'bind': '/logs', 'mode': 'rw'}},
        environment={'NEO4J_AUTH': 'neo4j/pass'},
        detach=True,
    )

    inspection = docker.api.inspect_container(container.id)
    docker_host = inspection['NetworkSettings']['IPAddress']
    http_port = 7474
    https_port = 7473
    bolt_port = 7687

    delay = 0.1
    for i in range(10):
        s = socket.socket()
        try:
            s.connect((docker_host, http_port))
        except OSError:
            time.sleep(delay)
            delay *= 2
        else:
            break
        finally:
            s.close()
    else:
        pytest.fail("Cannot start neo4j server")

    yield {
        'params': {
            'host': docker_host,
            'http_port': http_port,
            'https_port': https_port,
            'bolt_port': bolt_port,
            'auth': ('neo4j', 'pass'),
        }
    }

    container.kill(signal=9)
    container.remove(force=True)


@pytest.fixture
def neo4j_params(neo4j_server):
    return dict(**neo4j_server['params'])


@pytest.fixture
def neo4j(loop, neo4j_params):
    print('http://{host}:{http_port}'.format_map(neo4j_params))
    neo4j = Neo4j(url='http://{host}:{http_port}'.format_map(neo4j_params),
                  auth=neo4j_params['auth'],
                  loop=loop)

    yield neo4j

    loop.run_until_complete(neo4j.close())
