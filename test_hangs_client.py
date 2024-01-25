import asyncio
import random
from asyncio import Task

from aiohttp import ClientSession
from aiohttp.client import _RequestContextManager


async def just_request(inx):
    session = ClientSession()
    resp = await session.get(f'http://127.0.0.1:7831/?inx={inx}', timeout=30)
    print(await resp.text())
    await session.close()


if __name__ == '__main__':
    reqs = []
    for i in range(50):
        reqs.append(just_request(i))

    asyncio.get_event_loop().run_until_complete(asyncio.gather(*reqs))
