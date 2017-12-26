async def test_neo4j_smoke(neo4j):
    data = await neo4j.data()

    assert 'node' in data
