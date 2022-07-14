from aiohttp import web
import aiohttp
from aiohttp.http_websocket import WSMessage

import json
import os

from word_server_util import generate_word

clients = []

correct_buffer = []
incorrect_buffer = []

buffer_max_length = 10


def message_handler(msg, **kwargs):
    data = json.loads(msg.data)
    if data['type'] == "requestWord":
        syllable = data['syllable']
        needed_letters = data['needed_letters']
        return {
            "type": "respondWord",
            "word": generate_word(syllable, needed_letters)
        }

    elif data['type'] == "correctWord":
        correct_buffer.append(data['word'])
        if len(correct_buffer) >= buffer_max_length:
            if not os.path.isfile("output/correct.json"):
                open('output/correct.json', 'w').close()
            with open("output/correct.json", 'r') as f:
                f_data = json.load(f)
            for i in correct_buffer:
                if i not in f_data:
                    f_data.append(i)

            print("Writing correct")
            with open("output/correct.json", 'w') as f:
                json.dump(f_data, f)
            with open("output/correct.txt", 'w') as f:
                f.write("\n".join(f_data))
            correct_buffer.clear()

    elif data['type'] == "incorrectWord":
        incorrect_buffer.append(data['word'])
        if len(incorrect_buffer) >= buffer_max_length:
            if not os.path.isfile("output/incorrect.json"):
                open('output/incorrect.json', 'w').close()
            with open("output/incorrect.json", 'r') as f:
                f_data = json.load(f)
            for i in incorrect_buffer:
                if i not in f_data:
                    f_data.append(i)
            print("Writing incorrect")
            with open("output/incorrect.json", 'w') as f:
                json.dump(f_data, f)
            with open("output/incorrect.txt", 'w') as f:
                f.write("\n".join(f_data))
            incorrect_buffer.clear()


async def websocket_handler(request):
    clients.append(request)

    ws = web.WebSocketResponse()
    await ws.prepare(request)
    print(f"New client, Client #{len(clients)}")
    async for msg in ws:
        msg: WSMessage = msg
        response = message_handler(msg)

        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                if response:
                    await ws.send_str(json.dumps(response))
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())
    print('websocket connection closed')
    return ws


def run_server():
    app = web.Application()
    app.add_routes([web.get("/", websocket_handler)])

    web.run_app(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run_server()
