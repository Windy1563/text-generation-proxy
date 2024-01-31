# Strong references of https://gitgud.io/ihbs02/oai-reverse-proxy
import asyncio
import json
import os
from datetime import datetime

import aiofiles
import aiohttp
from aiohttp import web
from aiohttp.abc import Request

from util import Status, number_km

current_status = Status()
whole_status = Status()

title = "유즈의 이야기 정원"
desc = "유즈의 정원은 지금 활짝 열려 있어요! 여러분의 소중한 이야기들을 기다리고 있답니다. 하지만 가끔 유즈도 실수할 수 있으니, 조금만 넓은 마음으로 봐주세요. 곧 완벽한 이야기로 보답할 거예요!"
reqs = []
reqs_time = {}
last_request = "아직 요청이 없었어요. 냐~"

complete_reqs = []


def read_all(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


index_html = read_all("index.html").replace("{title}", title)


async def get_index(request: Request):
    return web.Response(content_type='text/html', text=index_html)


async def get_status(request: Request):
    global current_status, whole_status
    if len(reqs) == 0:
        current_request = "현재 진행중인 요청이 없어요. 냐~"
    else:
        current_request = reqs[0]["date"]

    while len(complete_reqs) != 0 and complete_reqs[0]['timestamp'] <= datetime.utcnow().timestamp() - 1800:
        del complete_reqs[0]

    return web.Response(content_type='text/json', text=json.dumps({
        "desc": desc,

        "queueCount": len(reqs),
        "lastRequest": last_request,
        "currentRequest": current_request,
        "recentRequestCount": len(complete_reqs),

        "inputTokenCount": number_km(current_status.input_token_count),
        "outputTokenCount": number_km(current_status.output_token_count),
        "requestCount": number_km(current_status.request_count),

        "wholeInputTokenCount": number_km(whole_status.input_token_count),
        "wholeOutputTokenCount": number_km(whole_status.output_token_count),
        "wholeRequestCount": number_km(whole_status.request_count),
    }))


async def option_index(request: Request):
    return web.Response(text='OK')


async def post_forward_request(request: Request):
    request_cap = {
        "request": request,
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    request_data = await request.json()
    if request_data['max_tokens'] > 500:
        return web.Response(status=502, headers={
            'Content-Type': 'text/json',
            'Access-Control-Allow-Origin': '*'
        }, text=json.dumps({"유즈의 메시지": "최대 응답 크기는 500개를 넘을 수 없습니다. 냥~"}))
    global reqs_time, last_request
    last_request = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'text/json',
            'Access-Control-Allow-Origin': '*'
        }
    )
    await response.prepare(request)
    try:
        reqs.append(request_cap)

        # Risu-AI가 긴 연결에도 대기하는것으로 보임
        ping_time = 0
        while request_cap != reqs[0]:
            await asyncio.sleep(0.1)
            ping_time += 0.1
            if ping_time >= 10:
                ping_time = 0
                # await response.write(b" ")

        async with aiohttp.ClientSession() as session:
            resp = await session.post('http://127.0.0.1:5000/v1/completions', json=request_data)
            resp_json = await resp.json()

        whole_status.calc_openai_response(resp_json)
        complete_info = current_status.calc_openai_response(resp_json)
        complete_reqs.append(complete_info)

        async with aiofiles.open('requests.jsonl', 'a', encoding='utf-8') as f:
            await f.write(json.dumps(complete_info) + "\n")

        # await response.write(b" ")
        await response.write(json.dumps(resp_json).encode('utf-8'))
        await response.write_eof()
        return response
    except Exception as e:
        print(f"Error: {e}")
    finally:
        reqs.remove(request_cap)
        await whole_status.save_status()


if __name__ == '__main__':
    whole_status.load_status()
    app = web.Application()
    app.add_routes([
        web.get("/", get_index),
        web.get("/status", get_status),
        web.options("/", option_index),
        web.post("/v1/completions", post_forward_request)
    ])

    web.run_app(app, port=7831, handler_cancellation=True)
