import sys

import aiohttp

PY_352 = sys.version_info >= (3, 5, 2)

AIOHTTP2 = aiohttp.__version__ >= '2.0.0'
