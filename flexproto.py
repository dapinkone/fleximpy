from enum import Enum
import nacl
import msgpack
from socket import create_connection
from datetime import datetime as dt
from time import sleep


class Datum(Enum):
    Auth = 0
    AuthResponse = 1
    Command = 2
    Message = 3
    Roster = 4
    User = 5


class flexclient:
    def __init__(self, ip="10.20.30.14", port=4321, username="test123"):
        self.username = username
        self.sock = create_connection((ip, port))
        self.sock.send(msgpack.packb("FLEX"))  # initial protocol header
        cmd = {"cmd": "AUTH", "payload": [username]}
        self.send_datum(cmd, Datum.Command)

        _, challenge_d = self.read_datum()
        print(challenge_d)
        self.send_auth_response(challenge_d[b"challenge"])
        self.request_roster()

    def mainloop(self):
        while True:
            d_type, d_data = self.read_datum()
            print(d_type, d_data)
            if d_type == Datum.Roster:
                self.roster = d_data

    def request_roster(self):
        self.send_datum({b"cmd": "ROSTER"}, Datum.Command)

    def send_auth_response(self, challenge):
        self.send_datum({b"challenge": challenge}, Datum.AuthResponse)

    def send_message(
        self, to, category="test", flags=["FLAGS?"], date=dt.now(), msgstr=""
    ):
        msg = {
            b"to": to,
            b"from": self.username,
            b"flags": flags,
            b"date": date,
            b"msg": msgstr,
        }
        d_type = Datum.Message  # type 3 = msg
        self.send_datum(msg, d_type)

    def send_datum(self, msg, d_type=0):
        out = msgpack.packb(msg, encoding="utf-8")
        size = len(out)
        self.sock.send(
            (d_type.value).to_bytes(1, "big") + size.to_bytes(2, "big") + out
        )

    def read_datum(self):
        d_type = int.from_bytes(self.sock.recv(1), "big")  # datum type
        d_size = int.from_bytes(self.sock.recv(2), "big")  # length of msgpack data
        datum = msgpack.unpackb(
            self.sock.recv(d_size)
        )  # TODO: proper exception handling
        return (Datum(d_type), datum)
