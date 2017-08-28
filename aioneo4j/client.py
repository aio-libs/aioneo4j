import asyncio
import collections

from yarl import URL

from .compat import PY_350
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

    @asyncio.coroutine
    def data(
        self,
        path='db/data',
        request_timeout=...,
    ):
        _, data = yield from self.transport.perform_request(
            'GET',
            path,
            request_timeout=request_timeout,
        )

        return data

    @asyncio.coroutine
    def cypher(
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

        _, data = yield from self.transport.perform_request(
            'POST',
            path,
            data=request,
            request_timeout=request_timeout,
        )

        return data

    @asyncio.coroutine
    def transaction_commit(
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

        _, data = yield from self.transport.perform_request(
            'POST',
            path,
            data=request,
            request_timeout=request_timeout,
        )

        return data

    @asyncio.coroutine
    def indexes(self, path='db/data/schema/index', request_timeout=...):
        _, data = yield from self.transport.perform_request(
            'GET',
            path,
            request_timeout=request_timeout,
        )

        return data

    @asyncio.coroutine
    def constraints(
        self,
        path='db/data/schema/constraint',
        request_timeout=...,
    ):
        _, data = yield from self.transport.perform_request(
            'GET',
            path,
            request_timeout=request_timeout,
        )

        return data

    @asyncio.coroutine
    def user_password(
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

        _, data = yield from self.transport.perform_request(
            'POST',
            path,
            data=request,
            request_timeout=request_timeout,
        )

        if set_auth:
            auth = username, password

            self.auth = auth

        return data

    def close(self):
        return self.transport.close()

    if PY_350:
        @asyncio.coroutine
        def __aenter__(self):  # noqa
            return self

        @asyncio.coroutine
        def __aexit__(self, *exc_info):  # noqa
            yield from self.close()
