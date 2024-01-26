# Strong references of https://gitgud.io/ihbs02/oai-reverse-proxy
import asyncio
import json
import os
from datetime import datetime

import aiofiles
import aiohttp
from aiohttp import web
from aiohttp.abc import Request


def number_km(number):
    if number < 1000:
        return str(number)
    elif number < 1000000:
        number = round(number / 1000, 3)
        return str(number) + "k"
    else:
        number = round(number / 1000000, 3)
        return str(number) + "m"


class Status:
    def __init__(self):
        self.input_token_count = 0
        self.output_token_count = 0
        self.request_count = 0

    def load_status(self, path='status.json'):
        if not os.path.exists(path):
            return
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        data = json.loads(text)
        self.input_token_count = data['input_token_count']
        self.output_token_count = data['output_token_count']
        self.request_count = data['request_count']

    async def save_status(self, path='status.json'):
        async with aiofiles.open(path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps({
                "input_token_count": self.input_token_count,
                "output_token_count": self.output_token_count,
                "request_count": self.request_count
            }))

    def calc_openai_response(self, resp_json):
        self.input_token_count += resp_json['usage']['prompt_tokens']
        self.output_token_count += resp_json['usage']['completion_tokens']
        self.request_count += 1
        return {
            "input_token_count": resp_json['usage']['prompt_tokens'],
            "output_token_count": resp_json['usage']['completion_tokens'],
            "timestamp": datetime.utcnow().timestamp()
        }


current_status = Status()
whole_status = Status()

title = "유즈의 행복을 나누는 곳"
desc = """
실수가 있어도, 유즈가 정성을 다해 준비했다는 것을 기억해주세요. 냐~
"""
reqs = []
reqs_time = {}
last_request = "아직 요청이 없었어요. 냐~"

complete_reqs = []


def read_all(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


index_html = read_all("index.html").replace("{title}", title).replace("{desc}", desc)


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
