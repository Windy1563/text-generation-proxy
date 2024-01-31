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
desc = "지금은 유즈가 잠시 쉬고 있는 시간이에요. 푹신한 담요 속에서 충전하는 중이랍니다! 조금 후에 다시 돌아올테니 그때까지 기다려 주세요."

reqs = []
reqs_time = {}
reqs_endpoints = []

last_request = "아직 요청이 없었어요. 냐~"

complete_reqs = []



def read_all(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


index_html = read_all("index.html").replace("{title}", title).replace("{desc}", desc)

reqs_endpoints = []

endpoints = []
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
    except Exception as e:
        print(e)
        return 'fail'
    finally:
        try:
            reqs_endpoints.remove(request)
        except:
            pass


async def get_index(request: Request):
    return web.Response(content_type='text/html', text=index_html)


async def get_status(request: Request):
    global current_status, whole_status
    if len(reqs) == 0:
        current_request = "현재 진행중인 요청이 없어요. 냐~"
    else:
        current_request = reqs[0]["date"]

    while len(complete_reqs) != 0 and complete_reqs[0]['end_time'] <= datetime.utcnow().timestamp() - 1800:
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
    if len(endpoints) == 0:
        return web.Response(status=400, headers={
            'Content-Type': 'text/json',
            'Access-Control-Allow-Origin': '*'
        }, text=json.dumps({"유즈의 메시지": "지금은 유즈가 잠시 쉬고 있는 시간이에요. 푹신한 담요 속에서 충전하는 중이랍니다! 조금 후에 다시 돌아올테니 그때까지 기다려 주세요."}))

    request_cap = {
        "request": request,
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    request_data = await request.json()
    if request_data['max_tokens'] > 500:
        return web.Response(status=400, headers={
            'Content-Type': 'text/json',
            'Access-Control-Allow-Origin': '*'
        }, text=json.dumps({"유즈의 메시지": "최대 응답 크기는 500개를 넘을 수 없습니다. 냥~"}))
    global reqs_time, last_request
    last_request = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    taken_endpoint = 'fail'

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
        taken_endpoint = await wait_and_take_endpoint(request)
        if taken_endpoint == 'fail':
            raise

        start_time = datetime.utcnow().timestamp()

        async with aiohttp.ClientSession() as session:
            resp = await session.post(f'{taken_endpoint}/v1/completions', json=request_data)
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
        if taken_endpoint != 'fail':
            using_endpoints.remove(taken_endpoint)
        await whole_status.save_status()


async def get_admin_start(request: Request):
    global endpoints, current_status, index_html, desc

    if len(endpoints) != 0:
        endpoints = read_all('endpoints.txt').strip().split("\n")
        return web.Response(text="Already started, just refresh endpoints.")

    endpoints = read_all('endpoints.txt').strip().split("\n")

    current_status = Status()
    desc = "유즈의 정원은 지금 활짝 열려 있어요! 여러분의 소중한 이야기들을 기다리고 있답니다. 하지만 가끔 유즈도 실수할 수 있으니, 조금만 넓은 마음으로 봐주세요. 곧 완벽한 이야기로 보답할 거예요!"

    return web.Response(text="OK!")


async def get_admin_stop(request: Request):
    global endpoints, index_html, desc
    endpoints = []

    desc = "지금은 유즈가 잠시 쉬고 있는 시간이에요. 푹신한 담요 속에서 충전하는 중이랍니다! 조금 후에 다시 돌아올테니 그때까지 기다려 주세요."

    return web.Response(text="OK!")


if __name__ == '__main__':
    whole_status.load_status()
    app = web.Application()

    token = read_all('token').strip()

    app.add_routes([
        web.get(f"/admin/{token}/start", get_admin_start),
        web.get(f"/admin/{token}/stop", get_admin_stop),
        web.get("/", get_index),
        web.get("/status", get_status),
        web.options("/", option_index),
        web.post("/v1/completions", post_forward_request)
    ])

    web.run_app(app, port=7831, handler_cancellation=True)
