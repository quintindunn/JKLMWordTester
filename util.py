import random

import requests

import websocket
from colorama import init, Fore

init()  # Colorama init


def generate_user_token():
    digits = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-"
    user_token = ""
    for i in range(16):
        user_token += random.choice(digits)
    return user_token


def get_ws_url(code: str) -> str:
    return requests.post("https://jklm.fun/api/joinRoom", json={"roomCode": code}).json()['url'].replace("https", "wss")


class Socket(websocket.WebSocket):
    def __int__(self, **_):
        super().__init__(**_)
        self.debug_name = None

    def send_message(self, msg, **kwargs):
        if self.debug_name:
            if msg not in ("3", "42[\"joinRound\"]"):
                print(f"{self.debug_name} SEND: ", msg, Fore.RESET)
        self.send(msg, **kwargs)

    def recv_msg(self):
        data = self.recv()
        if self.debug_name:
            if data not in ("2", "42[\"joinRound\"]"):
                print(f"{self.debug_name} RECV: ", data)
        return data
