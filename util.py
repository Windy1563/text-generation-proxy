import json
import os
from datetime import datetime

import aiofiles


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