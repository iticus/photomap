"""
Created on 2022-02-25

@author: iticus
"""

import logging
from typing import Callable

import aiohttp_jinja2
from aiohttp import web, web_exceptions
from multidict import CIMultiDict

# from aiohttp_session import get_session

logger = logging.getLogger(__name__)


@web.middleware
async def error_middleware(request: web.Request, handler: Callable) -> web.Response:
    """
    Try to handle the request and render a custom error page if an exception occurs
    :param request: web Request to handle
    :param handler: handler to execute
    :return: web response object
    """
    try:
        if "g_state" in request.headers.get("Cookie", ""):
            headers = dict(request.headers)  # fixes: https://github.com/python/cpython/issues/92936
            headers["Cookie"] = headers["Cookie"].replace('"', "")
            request = request.clone(headers=CIMultiDict(headers))
        response = await handler(request)
        if response.status != 500:
            return response
        message = response.message
    except web_exceptions.HTTPNotFound:
        logging.warning("cannot find page %s, 404", request.path)
        message = "requested page not found"
    except Exception as exc:  # pylint: disable=broad-exception-caught
        if request.method == "POST" and request.path.startswith("/upload"):
            logger.error("error processing upload: %s", exc, exc_info=True)
            return web.json_response({"status": "error", "message": f"{exc}"}, status=400)
        if not (request.raw_path.startswith("/media") or request.raw_path.endswith(".map")):
            logger.error("error processing request: %s", request.raw_path, exc_info=True)
        message = str(exc)
    return aiohttp_jinja2.render_template("error.html", request, context={"message": message}, status=500)
