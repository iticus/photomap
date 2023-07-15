"""
Created on 2023-01-07

@author: iticus
"""

import asyncio
import os

import aiohttp.web
import pytest
from aiohttp.test_utils import TestClient

from main import make_app

pytest_plugins = "aiohttp.pytest_plugin"  # pylint: disable=invalid-name


@pytest.fixture
def photomap_app(loop: asyncio.AbstractEventLoop, aiohttp_client: TestClient) -> aiohttp.web.Application:
    """
    Create aiohttp Application instance to be used in tests
    :param loop: asyncio loop
    :param aiohttp_client: aiohttp client
    :return: None
    """
    app = make_app()
    return loop.run_until_complete(aiohttp_client(app))
