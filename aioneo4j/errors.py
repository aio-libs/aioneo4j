import asyncio


class Error(Exception):
    pass


class SerializationError(Error):
    pass


class TransportError(Error):
    pass


class TimeoutError(asyncio.TimeoutError, TransportError):
    pass


class ClientError(Error):

    @property
    def errors(self):
        return self.args[0]

# TODO: specific error like Neo.ClientError.Security.Unauthorized
