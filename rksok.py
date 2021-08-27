#!/usr/bin/env python3
import sys
import re
from enum import Enum
import asyncio


class Method(Enum):
    GET = 'ОТДОВАЙ'
    PUT = 'ЗОПИШИ'
    DELETE = 'УДОЛИ'


class ResponseStatus(Enum):
    OK = "НОРМАЛДЫКС"
    NOT_FOUND = "НИНАШОЛ"
    BAD_REQUEST = "НИПОНЯЛ"


METHODS = (Method.GET.value, Method.PUT.value, Method.DELETE.value)
PROTOCOL = 'РКСОК/1.0'

PROXY_HOST = 'vragi-vezde.to.digital'
PROXY_PORT = 51624
SERVER_NAME = '127.0.0.1'
SERVER_PORT = 8888

BAD_REQUEST_RESPONSE = f'{ResponseStatus.BAD_REQUEST.value} {PROTOCOL}\r\n\r\n'
NOT_FOUND_RESPONSE = f'{ResponseStatus.NOT_FOUND.value} {PROTOCOL}\r\n\r\n'
OK_RESPONSE = f'{ResponseStatus.OK.value} {PROTOCOL}\r\n'


# requests = sys.stdin.read().split('#')

# TODO add logs, add file or sqlite or reddis

class PhoneBook:
    def __init__(self):
        self.phonebook = {}

    def get_phones_by_name(self, name):
        return self.phonebook.get(name)

    def delete_entry_by_name(self, name):
        return self.phonebook.pop(name, None)

    def add_or_update_entry(self, name, phones=None):
        self.phonebook[name] = phones
        return self.phonebook[name]


async def send_request_to_proxy_server(message):
    reader, writer = await asyncio.open_connection(PROXY_HOST, PROXY_PORT)

    print('a')

    request = f'АМОЖНА? {PROTOCOL}\r\n{message}'
    print('b')
    writer.write(request.encode())
    print('c')
    await writer.drain()
    print('d')

    data = await reader.read(8 * 1024 * 1024)
    print('e')

    writer.close()
    print('f')
    await writer.wait_closed()
    print('g')

    return data.decode()

phonebook = PhoneBook()

n = 0

async def handle_echo(reader, writer):
    response = BAD_REQUEST_RESPONSE
    
    try:
        data = b''
        while True:
            chunk = await reader.read(1024)
            data += chunk
            if not chunk or chunk.endswith(b'\r\n\r\n'):
                break
   
    except Exception as e:
        print(type(e), e.args)


        # data_extra = await reader.readuntil(b'\r\n\r\n')
        # print(f"Extra: {data_extra.decode()!r}")
        # exit()

    else:
        message = data.decode()
        global n 
        n += 1
        print(f"Received: {n} {message!r} {len(message)}")

        # TODO move into fn
        if message.endswith('\r\n\r\n'):
            message_lines = message.rstrip('\r\n\r\n').split('\r\n')
            if re.match(r'^(ОТДОВАЙ|ЗОПИШИ|УДОЛИ) ', message_lines[0]) and message_lines[0].endswith(PROTOCOL):
                response_from_proxy_server = await send_request_to_proxy_server(message)
                print(f'{response_from_proxy_server!r}')
                # TODO move into fn (return str or None)
                if response_from_proxy_server.startswith('НИЛЬЗЯ'):
                    response = response_from_proxy_server
                elif response_from_proxy_server.startswith('МОЖНА'):
                        entry_name = re.match(
                            r'^(ОТДОВАЙ|ЗОПИШИ|УДОЛИ) (.+) РКСОК/1.0', message_lines[0]).group(2)
                        if len(entry_name) <= 30:
                            if message.startswith('ОТДОВАЙ'):
                                phones = phonebook.get_phones_by_name(entry_name)
                                print(entry_name, phones)
                                response = OK_RESPONSE + phones + '\r\n\r\n' if phones else NOT_FOUND_RESPONSE

                            if message.startswith('УДОЛИ'):
                                response = f'{OK_RESPONSE}\r\n' if phonebook.delete_entry_by_name(
                                    entry_name) else NOT_FOUND_RESPONSE

                            if message.startswith('ЗОПИШИ'):
                                phonebook.add_or_update_entry(
                                    entry_name, '\r\n'.join(message_lines[1:]))
                                response = f'{OK_RESPONSE}\r\n'

    print(f"Send: {response!r}")
    writer.write(response.encode())
    await writer.drain()
    writer.close()


async def main():
    server = await asyncio.start_server(handle_echo, SERVER_NAME, SERVER_PORT)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()

asyncio.run(main())
