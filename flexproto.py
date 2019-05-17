from enum import Enum
import nacl
import msgpack
from socket import create_connection
from datetime import datetime as dt
from time import sleep
from typing import Callable, Iterable, Union, Optional, List
from threading import Thread
from binascii import hexlify


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
        ip: str = "10.20.30.14",
        port: int = 4321,
        username: str = "test" + str(dt.now()),
    ) -> None:
        self.pub_key = hexlify(bytes(username, encoding="utf-8"))
        self.sock = create_connection((ip, port))
        self.sock.send(msgpack.packb("FLEX"))  # initial protocol header
        cmd = {"cmd": "AUTH", "payload": [self.pub_key]}
        self.send_datum(cmd, Datum.Command)

        _, challenge_d = self.read_datum()
        print(challenge_d)
        self.send_auth_response(challenge_d["challenge"])
        self.request_roster()
        _, _ = self.read_datum()  # user datum?

        Thread(target=self.mainloop).start()

    def mainloop(self):
        while True:
            try:
                d_type, d_data = self.read_datum()
            except Exception as e:
                print(e)
                continue
            print(d_type, d_data)
            if d_type == Datum.Roster:
                self.roster = d_data
            if d_type == Datum.Message:
                self.got_message_callback(d_data)

    def got_message_callback(self, d_data):
        pass

    def request_roster(self):
        self.send_datum({"cmd": "ROSTER"}, Datum.Command)

    def send_auth_response(self, challenge: str):
        self.send_datum({"challenge": challenge}, Datum.AuthResponse)

    def send_message(
        self,
        to: str,
        category: str = "test",
        flags: Optional[List[str]] = ["FLAGS?"],
        message: str = "",
    ):
        to = hexlify(bytes(to, encoding="utf-8"))

        msg = {
            "to": to,
            "from": self.username,
            "flags": flags,
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
