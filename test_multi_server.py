import asyncio

from aiohttp import web
from aiohttp.abc import Request

reqs_endpoints = []

endpoints = ['1', '2', '3']
using_endpoints = []


def can_use_endpoint(endpoint):
    for using in using_endpoints:
        if using == endpoint:
            return False

    return True


def take_left_endpoint():
    for endpoint in endpoints:
        if can_use_endpoint(endpoint):
            using_endpoints.append(endpoint)
            return endpoint


async def wait_and_take_endpoint(request):
    try:
        reqs_endpoints.append(request)

        while reqs_endpoints[0] != request:
            await asyncio.sleep(0.1)

        while len(endpoints) == len(using_endpoints):
            await asyncio.sleep(0.1)

        return take_left_endpoint()
    except:
        return 'fail'
    finally:
        try:
            reqs_endpoints.remove(request)
        except:
            pass


async def get_index(request: Request):
    inx = request.rel_url.query['inx']
    print(f"Incoming: {inx}")
    taken_endpoint = ''
    try:
        taken_endpoint = await wait_and_take_endpoint(request)
        print(f"Taken: {inx}")
        await asyncio.sleep(1)
        print(f"Done: {inx}")
        return web.Response(text=taken_endpoint)
    finally:
        if taken_endpoint != '':
            using_endpoints.remove(taken_endpoint)


if __name__ == '__main__':
    app = web.Application()

    app.add_routes([
        web.get("/", get_index),
    ])
    web.run_app(app, port=7831, handler_cancellation=True)
