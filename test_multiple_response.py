import asyncio
import json

from aiohttp import web
from aiohttp.abc import Request


async def fake_response(request: Request):
    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'text/json',
            'Access-Control-Allow-Origin': '*'
        }
    )
    await response.prepare(request)

    await response.write(json.dumps(
        {"id": "conv-1706626279959506432", "object": "text_completion", "created": 1706626279,
         "model": "rAIfle_BagelMIsteryTour-v2-8x7B-exl2-rpcal_6b6h", "choices": [{"index": 0, "finish_reason": "stop",
                                                                                  "text": " \nAMaria's expression softened at Lucas's confession, her eyes filled with understanding and empathy. She gently placed her hand on his shoulder, offering a comforting squeeze. \"Forgiveness is a difficult journey, Lucas. It's not something that happens overnight. It's a process, a journey of the heart. Sometimes, it takes time to heal, to truly let go of the pain. But remember, God is always there to help us, to guide us on this journey.\"\n\nShe paused, considering her words carefully. \"It's not about placing blame, my child. It's about understanding, about finding peace. If you've offered your forgiveness, then you've done your part. But if you still feel hurt, that's normal. It's okay to acknowledge your feelings. Just remember, God is with you in this struggle, and so am I.\"\n\nMaria's hand remained on Lucas's shoulder, a silent promise of her support and understanding. \"Take your time, Lucas. It's okay to feel hurt, it's okay to feel confused. Just remember, you're not alone in this.\"",
                                                                                  "logprobs": {"top_logprobs": [{}]}},
                                                                                 {"index": 1, "finish_reason": "stop",
                                                                                  "text": " \nBMaria's expression softened at Lucas's confession, her eyes filled with understanding and empathy. She gently placed her hand on his shoulder, offering a comforting squeeze. \"Forgiveness is a difficult journey, Lucas. It's not something that happens overnight. It's a process, a journey of the heart. Sometimes, it takes time to heal, to truly let go of the pain. But remember, God is always there to help us, to guide us on this journey.\"\n\nShe paused, considering her words carefully. \"It's not about placing blame, my child. It's about understanding, about finding peace. If you've offered your forgiveness, then you've done your part. But if you still feel hurt, that's normal. It's okay to acknowledge your feelings. Just remember, God is with you in this struggle, and so am I.\"\n\nMaria's hand remained on Lucas's shoulder, a silent promise of her support and understanding. \"Take your time, Lucas. It's okay to feel hurt, it's okay to feel confused. Just remember, you're not alone in this.\"",
                                                                                  "logprobs": {"top_logprobs": [{}]}}],
         "usage": {"prompt_tokens": 3947, "completion_tokens": 251, "total_tokens": 4198}}).encode('utf-8'))
    await response.write_eof()
    return response


if __name__ == '__main__':
    app = web.Application()

    app.add_routes([
        web.post("/v1/completions", fake_response)
    ])
    web.run_app(app, port=7831, handler_cancellation=True)
