import sys

import aiohttp

PY_350 = sys.version_info >= (3, 5, 0)

AIOHTTP2 = aiohttp.__version__ >= '2.0.0'
