#!/usr/bin/env python3
import re
from enum import Enum
import asyncio
from typing import Optional
from loguru import logger
from phonebook import Phonebook


class RequestMethod(Enum):
    GET = "ОТДОВАЙ"
    PUT = "ЗОПИШИ"
    DELETE = "УДОЛИ"


class ResponseStatus(Enum):
    OK = "НОРМАЛДЫКС"
    NOT_FOUND = "НИНАШОЛ"
    BAD_REQUEST = "НИПОНЯЛ"


PROTOCOL = "РКСОК/1.0"

PROXY_HOST = "vragi-vezde.to.digital"
PROXY_PORT = 51624
SERVER_NAME = "0.0.0.0"
SERVER_PORT = 8888


async def check_with_proxy_server(message: str) -> Optional[str]:
    """Returns a response from the proxy server if the request is denied, otherwise None"""
    reader, writer = await asyncio.open_connection(PROXY_HOST, PROXY_PORT)

    request = f"АМОЖНА? {PROTOCOL}\r\n{message}"
    writer.write(request.encode())
    await writer.drain()

    response = (await reader.read()).decode()
    logger.info(f"Proxy: {response!r}")

    writer.close()
    await writer.wait_closed()

    return response if response.startswith("НИЛЬЗЯ") else None


def format_response(status: ResponseStatus, data: Optional[str] = None) -> str:
    if data:
        return f"{status.value} {PROTOCOL}\r\n{data}\r\n\r\n"
    else:
        return f"{status.value} {PROTOCOL}\r\n\r\n"


phonebook = Phonebook()

lock = asyncio.Lock()


async def handle_message(message: str) -> str:
    if message.endswith("\r\n\r\n"):
        message_lines = message.rstrip("\r\n\r\n").split("\r\n")
        methods = "|".join([x.value for x in RequestMethod])
        match = re.match(rf"^({methods}) (.+) РКСОК/1.0", message_lines[0])

        if match:
            proxy_response = await check_with_proxy_server(message)
            if proxy_response:
                return proxy_response

            request_method, entry_name = match.group(1), match.group(2)

            if len(entry_name) <= 30:
                logger.info(request_method)
                if request_method == RequestMethod.GET.value:
                    async with lock:
                        phones = phonebook.get_phones_by_name(entry_name)
                        return (
                            format_response(ResponseStatus.OK, phones)
                            if phones
                            else format_response(ResponseStatus.NOT_FOUND)
                        )
                elif request_method == RequestMethod.DELETE.value:
                    async with lock:
                        deleted = phonebook.delete_entry_by_name(entry_name)
                        return (
                            format_response(ResponseStatus.OK)
                            if deleted
                            else format_response(ResponseStatus.NOT_FOUND)
                        )
                elif request_method == RequestMethod.PUT.value:
                    async with lock:
                        phonebook.add_or_update_entry(
                            entry_name, "\r\n".join(message_lines[1:])
                        )
                        return format_response(ResponseStatus.OK)

    return format_response(ResponseStatus.BAD_REQUEST)


@logger.catch
async def rksok_handler(reader, writer):
    data = b""
    while True:
        chunk = await reader.read(1024)
        data += chunk
        if not chunk or chunk.endswith(b"\r\n\r\n"):
            break

    message = data.decode()
    logger.info(f"Received: {message[:30]!r}... {len(message)} chars")

    response = await handle_message(message)

    writer.write(response.encode())
    logger.info(f"Sent: {response[:30]!r}... {len(response)} chars")
    await writer.drain()
    writer.close()


async def main():
    logger.add(
        "rksok.log",
        format="{time} {level} {message}",
        level="INFO",
        rotation="100 KB",
        compression="zip",
    )
    server = await asyncio.start_server(rksok_handler, SERVER_NAME, SERVER_PORT)

    address = server.sockets[0].getsockname()
    logger.info(f"Serving on {address}")

    async with server:
        await server.serve_forever()


asyncio.run(main())
