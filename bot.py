import json
import threading
import time

import requests
import ssl

from colorama import init, Fore

from util import generate_user_token, get_ws_url, Socket

debug_mode = False

init()  # Colorama init

bot_lobbies = []

class Bot:
    def __init__(self, room=None, nickname="Bot", auto_join_room=True, word_ws_url="ws://127.0.0.1:8000"):
        self.room_id = room
        self.nickname = nickname

        self.auto_join_room = auto_join_room

        self.ws_url = None if not self.room_id else get_ws_url(self.room_id)
        self.word_ws_url = word_ws_url
        self.token = None

        self.chat_ws = None
        self.game_ws = None
        self.word_ws = None

        self.chat_room_info = None
        self.game_room_info = None

        self.self_peer_id = None

        self.turn = None
        self.syllable = None
        self.needed_letters = None

    def create_lobby(self):
        if not self.token:
            self.token = generate_user_token()
        data = {"name": "room",  # Dynamic
                "isPublic": False,  # Static
                "gameId": "bombparty",  # Static
                "creatorUserToken": self.token  # Dynamic
                }
        request = requests.post("https://jklm.fun/api/startRoom", json=data)

        if request.status_code != 200:
            raise ConnectionError("Something went wrong creating the room...")

        data = request.json()
        self.room_id = data['roomCode']
        self.ws_url = data['url'].replace("https://", "wss://")

    def join_chat(self, *args, **kwargs):
        """Join chat websocket, **REQUIRED**"""
        self.chat_ws = Socket(sslopt={"cert_reqs": ssl.CERT_NONE}, debug=True)
        self.chat_ws.debug_name = f"{Fore.GREEN}ChatSock" if debug_mode else None
        self.chat_ws.connect(self.ws_url + "/socket.io/?EIO=4&transport=websocket")

        if not self.token:
            self.token = generate_user_token()

        # Static packets
        self.chat_ws.recv_msg()
        self.chat_ws.send_message("40")
        self.chat_ws.recv_msg()

        # Join packets
        data = ["joinRoom",
                {"roomCode": self.room_id.upper(),
                 "userToken": self.token,
                 "nickname": self.nickname,
                 "language": "en-US"
                 }
                ]
        data = "420" + json.dumps(data)
        self.chat_ws.send_message(data)
        self.chat_room_info = json.loads(self.chat_ws.recv_msg().split("430")[1])
        while True:
            if self.chat_ws.recv_msg() == "2":  # Keep-Alive
                self.chat_ws.send_message("3")
                continue

    def join_game(self, *args, **kwargs):
        """Join game websocket, **REQUIRED**"""
        self.game_ws = Socket(sslopt={"cert_reqs": ssl.CERT_NONE}, debug=True)
        self.game_ws.debug_name = f"{Fore.BLUE}GameSock" if debug_mode else None
        self.game_ws.connect(self.ws_url + "/socket.io/?EIO=4&transport=websocket")

        if not self.token:
            self.token = generate_user_token()

        # Static packets
        self.game_ws.recv_msg()
        self.game_ws.send_message("40")
        self.game_ws.recv_msg()

        # Join packets
        self.game_ws.send_message("42" + json.dumps(["joinGame", "bombparty", self.room_id, self.token], separators=(',', ':')))
        self.game_room_info = json.loads(self.game_ws.recv_msg().split("42")[1])[1]
        self.self_peer_id = self.game_room_info['selfPeerId']

        self.needed_letters = list("abcdefghijklmnopqrstuvwxyz")
        previous_msg = ""
        while True:
            if self.auto_join_room:
                self.join_round()
                self.game_ws.send_message('42["startRoundNow"]')

            if self.turn:
                word = self.get_word()
                self.set_word(word)
                time.sleep(1)
                self.turn = False

            msg = self.game_ws.recv_msg()
            if msg == "2":  # Keep-Alive
                self.game_ws.send_message("3")
                continue

            if not msg.startswith("42["):
                print(msg)
                continue

            msg = msg.split("42", 1)[1]
            msg_type = json.loads(msg)[0]
            if msg_type == "setPlayerWord":
                pass
            elif msg_type == "correctWord":
                self.handle_correct(msg, previous_msg)

            elif msg_type == "nextTurn":
                self.handle_next_turn(msg, previous_msg)

            elif msg_type == "livesLost":
                pass

            elif msg_type == "failWord":
                self.handle_fail(msg, previous_msg)

            elif msg_type == "setMilestone":
                self.handle_milestone(msg, previous_msg)

            previous_msg = msg

    def join_round(self):
        self.game_ws.send_message("42[\"joinRound\"]")

    def handle_fail(self, msg, previous):
        if not self.word_ws:
            self.word_ws = Socket()
            self.word_ws.debug_name = f"{Fore.MAGENTA}WordSock" if debug_mode else None
            self.word_ws.connect(self.word_ws_url)

        previous = json.loads(previous)[-1]
        msg = json.loads(msg)
        if msg[1] == self.self_peer_id:
            self.turn = True

        self.word_ws.send_message(json.dumps({
            "type": "incorrectWord",
            "word": previous
        }))
        print(f"Not a word: {previous}")

    def handle_correct(self, msg, previous):
        if not self.word_ws:
            self.word_ws = Socket()
            self.word_ws.debug_name = f"{Fore.MAGENTA}WordSock" if debug_mode else None
            self.word_ws.connect(self.word_ws_url)

        previous = json.loads(previous)[-1]
        msg = json.loads(msg)
        bonus_letters = msg[1]['bonusLetters']
        if msg[1]['playerPeerId'] == self.self_peer_id:
            self.needed_letters = list("abcdefghijklmnopqrstuvwxyz")
            for letter in bonus_letters:
                self.needed_letters.remove(letter)


        self.word_ws.send_message(json.dumps({
            "type": "correctWord",
            "word": previous
        }))
        print(f"Correct Word: {previous}")

    def handle_milestone(self, msg, previous):
        msg = json.loads(msg)[1]
        if msg['name'] == "round":
            self.syllable = msg['syllable']
            self.turn = msg['currentPlayerPeerId'] == self.self_peer_id
            if self.turn:
                self.needed_letters = list("abcdefghijklmnopqrstuvwxyz")

    def handle_next_turn(self, msg, previous):
        msg = json.loads(msg)
        self.syllable = msg[2]
        self.turn = msg[1] == self.self_peer_id

    def get_word(self):
        if not self.word_ws:
            self.word_ws = Socket()
            self.word_ws.debug_name = f"{Fore.MAGENTA}WordSock" if debug_mode else None
            self.word_ws.connect(self.word_ws_url)

        self.word_ws.send_message(json.dumps({
            "type": "requestWord",
            "syllable": self.syllable,
            "needed_letters": self.needed_letters
        }))
        return json.loads(self.word_ws.recv_msg())['word']

    def set_word(self, word):
        if word:
            self.game_ws.send("42" + json.dumps(['setWord', word, True]))
        else:
            print("No word found")

    def __str__(self):
        return f"{self.room_id=} | {self.ws_url=} | {self.token=}"


def create_bot_lobby(**kwargs):
    bot = Bot(**kwargs)
    bot.create_lobby()

    lobby_id = bot.room_id
    ws_url = bot.ws_url
    bot_lobbies.append(f"https://jklm.fun/{lobby_id}")

    threading.Thread(target=bot.join_chat, daemon=True).start()
    time.sleep(0.5)
    threading.Thread(target=bot.join_game, daemon=True).start()

    bot2 = Bot(room=lobby_id)
    bot2.ws_url = ws_url

    threading.Thread(target=bot2.join_chat, daemon=True).start()
    time.sleep(0.5)
    threading.Thread(target=bot2.join_game, daemon=True).start()


for i in range(40):
    try:
        create_bot_lobby(nickname="Tip")
        print(bot_lobbies)
        time.sleep(20)
    except Exception as e:
        print(e)
while True:
    pass
