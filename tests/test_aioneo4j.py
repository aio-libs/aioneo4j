import asyncio

import pytest


@pytest.mark.run_loop
@asyncio.coroutine
def test_neo4j_smoke(neo4j):
    data = yield from neo4j.data()

    assert bool(data)
