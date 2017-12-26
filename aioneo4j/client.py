import asyncio
import collections

from yarl import URL

from .transport import Transport


class Client:

    def __init__(
        self,
        url='http://127.0.0.1:7474/',
        auth=None,
        transport=Transport,
        request_timeout=...,
        *, loop=None
    ):
        if loop is None:
            loop = asyncio.get_event_loop()

        self.loop = loop

        url = URL(url)

        if url.user and url.password:
            auth = url.user, url.password

            url = url.with_user(None)

            # TODO: not sure is it needed
            url = url.with_password(None)

        self.transport = transport(
            url=url,
            auth=auth,
            request_timeout=request_timeout,
            loop=self.loop,
        )

    def get_auth(self):
        return self.transport.auth

    def set_auth(self, auth):
        self.transport.auth = auth

    auth = property(get_auth, set_auth)

    del get_auth, set_auth

    async def data(
        self,
        path='db/data',
        request_timeout=...,
    ):
        _, data = await self.transport.perform_request(
            'GET',
            path,
            request_timeout=request_timeout,
        )

        return data

    async def cypher(
        self,
        query,
        path='db/data/cypher',
        request_timeout=...,
        **params
    ):
        if not isinstance(query, collections.Mapping):
            request = {'query': query}

            if params:
                request['params'] = params
        else:
            assert not params

            request = query

        _, data = await self.transport.perform_request(
            'POST',
            path,
            data=request,
            request_timeout=request_timeout,
        )

        return data

    async def transaction_commit(
        self,
        *statements,
        path='db/data/transaction/commit',
        request_timeout=...  # noqa
    ):
        if (
            len(statements) == 1 and
            isinstance(statements[0], collections.Mapping) and
            'statements' in statements[0]
        ):
            request = statements[0]
        else:
            request = {'statements': []}

            for statement in statements:
                if not isinstance(statement, collections.Mapping):
                    statement = {'statement': statement}
                else:
                    if 'statement' not in statement:
                        raise ValueError

                request['statements'].append(statement)

        _, data = await self.transport.perform_request(
            'POST',
            path,
            data=request,
            request_timeout=request_timeout,
        )

        return data

    async def indexes(self, path='db/data/schema/index', request_timeout=...):
        _, data = await self.transport.perform_request(
            'GET',
            path,
            request_timeout=request_timeout,
        )

        return data

    async def constraints(
        self,
        path='db/data/schema/constraint',
        request_timeout=...,
    ):
        _, data = await self.transport.perform_request(
            'GET',
            path,
            request_timeout=request_timeout,
        )

        return data

    async def user_password(
        self,
        password,
        username='neo4j',
        path='user/{username}/password',
        set_auth=False,
        request_timeout=...,
    ):
        path = path.format(
            username=username,
        )

        request = {'password': password}

        _, data = await self.transport.perform_request(
            'POST',
            path,
            data=request,
            request_timeout=request_timeout,
        )

        if set_auth:
            auth = username, password

            self.auth = auth

        return data

    async def close(self):
        await self.transport.close()

    async def __aenter__(self):  # noqa
        return self

    async def __aexit__(self, *exc_info):  # noqa
        await self.close()
