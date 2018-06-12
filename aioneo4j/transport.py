import asyncio
import collections
import json

import aiohttp
import async_timeout
from aiohttp import ClientError

from . import errors  # isort:skip  # noqa


class Transport:

    _auth = None

    def __init__(
        self,
        url,
        auth,
        encoder=json.dumps,
        decoder=json.loads,
        encoder_errors=(TypeError, ValueError),
        decoder_errors=(TypeError, ValueError),
        request_timeout=...,
        session=None,
        maxsize=20,
        use_dns_cache=False,
        *, loop
    ):
        self.loop = loop

        self.url = url

        self.auth = auth

        self.encoder = encoder
        self.decoder = decoder
        self.encoder_errors = encoder_errors
        self.decoder_errors = decoder_errors

        self.request_timeout = request_timeout

        self.session = session
        if self.session is None:
            self.session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(
                    limit=maxsize,
                    use_dns_cache=use_dns_cache,
                    loop=self.loop,
                ),
            )

    def get_auth(self):
        return self._auth

    def set_auth(self, auth):
        if auth is not None:
            if isinstance(auth, str):
                username, password = auth.split(':')
            elif isinstance(auth, collections.Sequence):
                username, password = auth

            auth = aiohttp.BasicAuth(
                login=username,
                password=password,
            )

        self._auth = auth

    auth = property(get_auth, set_auth)

    del get_auth, set_auth

    @property
    def headers(self):
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json; charset=UTF-8',
        }

    async def _perform_request(
        self,
        method,
        url,
        params=None,
        data=None,
    ):
        response = None

        try:
            response = await self.session.request(
                method,
                url,
                params=params,
                data=data,
                headers=self.headers,
                auth=self.auth,
                timeout=None,
            )

            text = await response.text()

            if not (200 <= response.status <= 300):
                extra = None

                try:
                    extra = self.decoder(text)
                except self.decoder_errors:
                    pass

                raise errors.ClientError(response.status, extra or text)

            return response.status, response.headers, text
        except ClientError as exc:
            raise errors.TransportError from exc
        finally:
            if response is not None:
                await response.release()

    async def perform_request(
        self,
        method,
        path,
        params=None,
        data=None,
        request_timeout=...,
    ):
        if data is not None:
            if not isinstance(data, (str, bytes)):
                try:
                    data = self.encoder(data)
                except self.encoder_errors as exc:
                    raise errors.SerializationError from exc

            if not isinstance(data, bytes):
                data = data.encode('utf-8')

        _url = self.url / path

        _coro = self._perform_request(method, _url, params=params, data=data)

        _request_timeout = request_timeout
        if request_timeout is ...:
            _request_timeout = self.request_timeout
        if _request_timeout is ...:
            _request_timeout = None

        try:
            with async_timeout.timeout(_request_timeout, loop=self.loop):
                status, headers, data = await _coro
        except asyncio.TimeoutError:
            raise errors.TimeoutError

        if data:
            try:
                data = self.decoder(data)
            except self.decoder_errors as exc:
                raise errors.SerializationError from exc

        # TODO: nested errors?
        if isinstance(data, collections.Mapping) and data.get('errors'):
            raise errors.ClientError(data['errors'])

        return status, data

    async def close(self):
        await self.session.close()
