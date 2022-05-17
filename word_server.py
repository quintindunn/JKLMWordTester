from aiohttp import web
import aiohttp
from aiohttp.http_websocket import WSMessage

import json
import os

import word_server_util
from word_server_util import generate_word

clients = []

correct_buffer = []
incorrect_buffer = []

buffer_max_length = 120

start_length = len(word_server_util.wordList)
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
            if not os.path.isfile("correct.json"):
                open('correct.json', 'w').close()
            with open("correct.json", 'r') as f:
                f_data = json.load(f)
            for i in correct_buffer:
                if i not in f_data:
                    f_data.append(i)

            print("Writing correct", "Words left:", len(word_server_util.wordList), "Tested: ", (start_length-len(word_server_util.wordList)))
            with open("correct.json", 'w') as f:
                json.dump(f_data, f)
            correct_buffer.clear()

    elif data['type'] == "incorrectWord":
        incorrect_buffer.append(data['word'])
        if len(incorrect_buffer) >= buffer_max_length:
            if not os.path.isfile("incorrect.json"):
                open('incorrect.json', 'w').close()
            with open("incorrect.json", 'r') as f:
                f_data = json.load(f)
            for i in incorrect_buffer:
                if i not in f_data:
                    f_data.append(i)
            print("Writing incorrect", "Words left:", len(word_server_util.wordList), "Tested: ", (start_length-len(word_server_util.wordList)))
            with open("incorrect.json", 'w') as f:
                json.dump(f_data, f)
            incorrect_buffer.clear()


async def websocket_handler(request):
    clients.append(request)

    ws = web.WebSocketResponse()
    await ws.prepare(request)
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
