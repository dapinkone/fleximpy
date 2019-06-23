from enum import Enum
import nacl
import msgpack
from socket import create_connection
from datetime import datetime as dt
from time import sleep
from typing import Callable, Iterable, Union, Optional, List
from threading import Thread
from binascii import hexlify, unhexlify


class Datum(Enum):
    Auth = 0
    AuthResponse = 1
    Command = 2
    Message = 3
    Roster = 4
    User = 5
    Status = 6


class flexclient:
    def __init__(
        self,
        ip: str = "127.0.0.1",
        port: int = 4321,
        username: str = "t" + chr(45 + int(str(dt.now())[-1])),
    ) -> None:
        self.username = username
        self.pub_key = hexlify(bytes("i need a key " + username, encoding="utf-8"))
        self.sock = create_connection((ip, port))
        self.sock.send(msgpack.packb("FLEX"))  # initial protocol header

        # build/send an auth command(not an auth datum) to inform server of our public key and username.
        cmd = {"cmd": "AUTH", "payload": [self.pub_key, self.username]}
        self.send_datum(cmd, Datum.Command)


        # _, _ = self.read_datum()  # user datum?
        self.roster = dict()
        # _, self.roster = self.read_datum()  # roster
        Thread(target=self.mainloop).start()

    def mainloop(self):
        while True:
            try:
                d_type, d_data = self.read_datum()
            except Exception as e:
                print(e)
                continue
            print(d_type, d_data)
            if d_type == Datum.Auth: # respond to auth challenge/response. request roster update.
                self.send_auth_response(d_data["challenge"])
                self.request_roster()
            if d_type == Datum.Roster:
                print("roster datum key type: " + str(type(d_data[0]["key"])))
                self.roster.update(
                    {user["key"]: {"alias": user["aliases"][0]} for user in d_data}
                )
                self.got_roster_callback()
            if d_type == Datum.Message:
                self.got_message_callback(d_data)
            if d_type == Datum.Status:
                # 10 for new user online
                # -10 for user gone offline.
                if d_data["status"] == 10:
                    self.request_user(d_data["payload"])
                self.got_status_callback(d_data)

            if d_type == Datum.User:
                if d_data["key"] not in self.roster:  # TODO: fix this. doesn't scale.
                    print("user recieved:" + d_data["aliases"][0])
                    self.roster[d_data["key"]] = {"alias": d_data["aliases"][0]}
                    self.got_roster_callback()
                else:
                    print("duplicate user:" + str(d_data))

    def request_user(self, key_str):
        print("requesting user: " + str(unhexlify(key_str), encoding="utf-8"))
        self.send_datum({"cmd": "GETUSER", "payload": [key_str]}, Datum.Command)

    def got_status_callback(self):
        pass

    def got_roster_callback(self):
        print("Roster recieved!")
        pass

    def got_message_callback(self, d_data):
        pass

    def request_roster(self):
        print("requesting roster!")
        self.send_datum({"cmd": "ROSTER"}, Datum.Command)

    def send_auth_response(self, challenge: str):
        self.send_datum({"challenge": challenge}, Datum.AuthResponse)

    def send_message(
        self,
        to: str,
        category: str = "test",
        flags: Optional[List[str]] = [],
        message: str = "",
    ):
        to = hexlify(to)

        msg = {
            "to": to,
            "from": self.pub_key,
            "flags": ["alias=" + self.username] + flags,
            "date": int(dt.now().timestamp()),
            "msg": message,
        }
        d_type: Datum = Datum.Message  # type 3 = msg
        self.send_datum(msg, d_type)

    def send_datum(self, msg: str, d_type: Datum):
        out: List[bytes] = msgpack.packb(msg, encoding="utf-8")
        size: int = len(out)
        self.sock.send(
            (d_type.value).to_bytes(1, "big") + size.to_bytes(2, "big") + out
        )

    def read_datum(self):
        try:
            d_type = Datum(int.from_bytes(self.sock.recv(1), "big"))  # datum type
            d_size = int.from_bytes(self.sock.recv(2), "big")  # length of msgpack data
            datum = msgpack.unpackb(
                self.sock.recv(d_size), encoding="utf-8"
            )  # TODO: proper exception handling
            return (d_type, datum)
        except Exception as e:
            print(e)
