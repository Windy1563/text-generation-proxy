import asyncio
import json

from aiohttp import web
from aiohttp.abc import Request


async def slow_response(request: Request):
    response = web.StreamResponse(
        status=502,
        reason='OK',
        headers={
            'Content-Type': 'text/json',
            'Access-Control-Allow-Origin': '*'
        }
    )
    await response.prepare(request)

    for i in range(6 * 10):
        print(f"Hanging {i}0 seconds...")
        await asyncio.sleep(10)
        # await response.write(b" ")

    await response.write(json.dumps({"유즈의 메시지": "지금 유즈는 자고 있어요. 냐~"}).encode('utf-8'))
    await response.write_eof()


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.post("/v1/completions", slow_response)
    ])

    web.run_app(app, port=7831, handler_cancellation=True)
