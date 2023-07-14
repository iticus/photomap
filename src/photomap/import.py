"""
Created on Sep 11, 2012

@author: iticus
"""

import asyncio
import logging
import os
from typing import Generator

from aiohttp import ClientSession

import settings

logger = logging.getLogger(__name__)
BASE_DIR = "/media/data/poze/"


def gather_file_list() -> Generator:
    """
    Generate list of image files from source folder
    """
    for dirpath, _, filenames in os.walk(BASE_DIR):
        for filename in filenames:
            if not filename.lower().endswith(".jpg") and not filename.lower().endswith(".jpeg"):
                # logging.info("skipping %s from %s" % (filename, dirpath))
                continue
            yield os.path.join(dirpath, filename)


async def upload_worker(path_queue: asyncio.Queue, session: ClientSession) -> None:
    """
    Pull file paths from the queue and upload them using the API
    :param path_queue: queue to pull file paths from
    :param session: client session to use for uploading
    """
    headers = {"Authentication": settings.SECRET}  # "Content-Type": content_type
    while True:
        file_path = await path_queue.get()
        logger.debug("uploading photo %s", file_path)
        try:
            file_handle = open(file_path, "rb")
            path, filename = os.path.split(file_path)
            request = await session.post(
                url="http://127.0.0.1:8000/upload/",
                data={"photo": file_handle.read(), "filename": filename, "path": path},
                headers=headers,
            )
            data = await request.json()
            logger.debug("uploaded photo %s: %s", filename, data)
            file_handle.close()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("cannot upload photo %s from %s: %s", filename, path, exc)
        path_queue.task_done()


async def main() -> None:
    """
    Main function to import photos using async parallel workers
    """
    session = ClientSession()
    path_queue: asyncio.Queue = asyncio.Queue()
    logger.info("creating workers")
    workers = [asyncio.create_task(upload_worker(path_queue, session=session)) for _ in range(4)]
    logger.info("populating queue")
    for filename in gather_file_list():
        await path_queue.put(filename)
    logger.info("queue populated")
    await path_queue.join()  # wait for all tasks to be processed
    await asyncio.sleep(2.0)
    logger.info("cancelling workers")
    for worker in workers:
        worker.cancel()
    await asyncio.gather(*workers, return_exceptions=True)
    logger.info("workers cancelled, closing client session")
    await session.close()
    logger.info("client session closed")
    await asyncio.sleep(2.0)


if __name__ == "__main__":
    logging.info("starting ioloop")
    asyncio.run(main())
