aioneo4j
==========

:info: asyncio client for neo4j

.. image:: https://img.shields.io/travis/wikibusiness/aioneo4j.svg
    :target: https://travis-ci.org/wikibusiness/aioneo4j

.. image:: https://img.shields.io/pypi/v/aioneo4j.svg
    :target: https://pypi.python.org/pypi/aioneo4j

Installation
------------

.. code-block:: shell

    pip install aioneo4j

Usage
-----

.. code-block:: python

    import asyncio

    from aioneo4j import Neo4j


    async def go():
        async with Neo4j('http://neo4j:neo4j@127.0.0.1:7474/') as neo4j:
            data = await neo4j.data()
            assert bool(data)


    loop = asyncio.get_event_loop()
    loop.run_until_complete(go())
    loop.close()
