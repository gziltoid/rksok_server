#!/usr/bin/env python3
import re
from enum import Enum
import asyncio
from typing import Optional


class Method(Enum):
    GET = "ОТДОВАЙ"
    PUT = "ЗОПИШИ"
    DELETE = "УДОЛИ"


class ResponseStatus(Enum):
    OK = "НОРМАЛДЫКС"
    NOT_FOUND = "НИНАШОЛ"
    BAD_REQUEST = "НИПОНЯЛ"


# METHODS = (Method.GET.value, Method.PUT.value, Method.DELETE.value)
PROTOCOL = "РКСОК/1.0"

PROXY_HOST = "vragi-vezde.to.digital"
PROXY_PORT = 51624
SERVER_NAME = "127.0.0.1"
SERVER_PORT = 8888

# TODO: REMOVE
BAD_REQUEST_RESPONSE = f"{ResponseStatus.BAD_REQUEST.value} {PROTOCOL}\r\n\r\n"
NOT_FOUND_RESPONSE = f"{ResponseStatus.NOT_FOUND.value} {PROTOCOL}\r\n\r\n"
OK_RESPONSE = f"{ResponseStatus.OK.value} {PROTOCOL}\r\n"


# TODO: return None if MOZHNA otherwise Some(str)
async def check_with_proxy_server(message) -> Optional[str]:
    '''Returns a response from the proxy server if the request is denied, otherwise None'''
    reader, writer = await asyncio.open_connection(PROXY_HOST, PROXY_PORT)

    request = f"АМОЖНА? {PROTOCOL}\r\n{message}"
    writer.write(request.encode())
    await writer.drain()

    data = await reader.read()

    writer.close()
    await writer.wait_closed()

    return data.decode()


phonebook = PhoneBook()


def format_response(status: ResponseStatus, data: Optional[str]) -> str:
    if data:
        f"{status.value} {PROTOCOL}\r\n{data}\r\n\r\n"
    else:
        f"{status.value} {PROTOCOL}\r\n\r\n"


async def handle_message(message):
    message_lines = message.rstrip("\r\n\r\n").split("\r\n")
            # TODO: try rf""
            # TODO: use 1 regex instead of 2
            # match = re.match(
            #             r"^(ОТДОВАЙ|ЗОПИШИ|УДОЛИ) (.+) РКСОК/1.0", message_lines[0]
            #         )
            # if match:
            #     name = match.group(2)
    if re.match(
                r"^(ОТДОВАЙ|ЗОПИШИ|УДОЛИ) ", message_lines[0]
            ) and message_lines[0].endswith(PROTOCOL):
        response_from_proxy_server = await check_with_proxy_server(message)
        if response_from_proxy_server.startswith("НИЛЬЗЯ"):
            response = response_from_proxy_server
        # TODO: check this inside send_request_to_proxy_server
        elif response_from_proxy_server.startswith("МОЖНА"):
            entry_name = re.match(
                        r"^(ОТДОВАЙ|ЗОПИШИ|УДОЛИ) (.+) РКСОК/1.0", message_lines[0]
                    ).group(2)
            if len(entry_name) <= 30:
                # TODO: extrach method name, not .startswith
                # TODO: use constants
                if message.startswith("ОТДОВАЙ"):
                    # log
                    phones = phonebook.get_phones_by_name(entry_name)
                    # TODO: Return
                    response = (
                                OK_RESPONSE + phones + "\r\n\r\n"
                                if phones
                                else NOT_FOUND_RESPONSE
                            )

                elif message.startswith("УДОЛИ"):
                    # TODO: remove ?:
                    response = (
                                f"{OK_RESPONSE}\r\n"
                                if phonebook.delete_entry_by_name(entry_name)
                                else NOT_FOUND_RESPONSE
                            )

                elif message.startswith("ЗОПИШИ"):
                    phonebook.add_or_update_entry(
                                entry_name, "\r\n".join(message_lines[1:])
                            )
                    response = f"{OK_RESPONSE}\r\n"
                
    # TODO: return error
    return response


async def rksok_handler(reader, writer):
    try:
        data = b""
        while True:
            chunk = await reader.read(1024)
            data += chunk
            if not chunk or chunk.endswith(b"\r\n\r\n"):
                break
    except Exception as e:
        # TODO: print ERROR
        print(type(e), e.args)
    else:
        message = data.decode()
        print(f"Received: {message!r} {len(message)}")

        # TODO: move into handle_message
        if message.endswith("\r\n\r\n"):
            response = await handle_message(message)
        else:
            # TODO: move into handle_message
            response = BAD_REQUEST_RESPONSE

        # TODO: ideally don't respond if there's an exception
        print(f"Sent: {response!r}")
        writer.write(response.encode())
        await writer.drain()
        writer.close()


async def main():
    server = await asyncio.start_server(rksok_handler, SERVER_NAME, SERVER_PORT)

    address = server.sockets[0].getsockname()
    print(f"Serving on {address}")

    async with server:
        await server.serve_forever()


asyncio.run(main())
