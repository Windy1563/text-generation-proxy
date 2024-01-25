import asyncio
import logging
import queue
import time

from aiohttp import web
from aiohttp.abc import Request

reqs = []


async def just_hangs(request: Request):
    inx = request.rel_url.query['inx']
    print(f"Incoming: {inx}")
    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'text/plain'
        }
    )
    await response.prepare(request)
    try:
        reqs.append(request)

        ping_time = 0
        while request != reqs[0]:
            await asyncio.sleep(0.1)
            ping_time += 0.1
            if ping_time >= 10:
                ping_time = 0
                print(f"Ping: {inx}")
                await response.write(b" ")
        await asyncio.sleep(10)
        print(f"Done: {inx}")
        await response.write(b"OK!")
        await response.write_eof()
        return response
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print(f"Removing: {inx}")
        reqs.remove(request)


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get("/", just_hangs)
    ])

    web.run_app(app, port=7831, handler_cancellation=True)
