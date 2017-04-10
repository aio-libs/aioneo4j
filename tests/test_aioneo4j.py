import asyncio

import pytest


@pytest.mark.run_loop
@asyncio.coroutine
def test_ping(neo4j):
    ping = yield from neo4j.data()

    assert bool(ping)
