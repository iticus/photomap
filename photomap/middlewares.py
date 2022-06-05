"""
Created on 2022-02-25

@author: iticus
"""

import logging
import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import get_session

logger = logging.getLogger(__name__)


@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        if response.status != 500:
            return response
        message = response.message
    except Exception as exc:
        if hasattr(exc, "status") and exc.status == 404:
            logger.error("cannot find resource: %s", request.raw_path)
            return aiohttp_jinja2.render_template("error.html", request, {}, status=404)
        if not (request.raw_path.startswith("/media") or request.raw_path.endswith(".map")):
            logger.error("error processing request: %s", request.raw_path, exc_info=True)
        message = str(exc)
    session = await get_session(request)
    context = {"session": session, "message": message}
    return aiohttp_jinja2.render_template("error.html", request, context, status=500)
