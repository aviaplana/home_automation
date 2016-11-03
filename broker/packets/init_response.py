import struct

from packet import Packet

'''
    Payload structure:

    | Hash |   Pipe  |
    |   2  |    1    |

'''


class InitResponsePacket(Packet):
    type = "init_response"

    def __init__(self):
        super(InitResponsePacket, self).__init__()
        self.id = 0
        self.hash = 0
        self.pipe = 0
        self.type = InitResponsePacket.type

    def interpret(self, received_buffer):
        values = struct.unpack("=1B1H1B", bytearray(received_buffer))
        self.id = values[0]
        self.hash = values[1]
        self.pipe = values[2]

    def get_values(self):
        return {"id": self.id, "hash": self.hash, "pipe": self.pipe}

    @staticmethod
    def create_buffer(n_id,  values):
        if len(values) < 2:
            print "Not enough values"
            return None

        return struct.pack("=4B1H3B", ord('\\'), ord('B'), Packet.packet_types[InitResponsePacket.type], n_id,
                           values["hash"], values["pipe"], ord('\\'), ord('E'))

    def get_buffer(self):
        return struct.pack("=4B1H3B", ord("\\"), ord("B"), Packet.packet_types[InitResponsePacket.type], self.id,
                           self.hash, self.pipe, ord("\\"), ord("E"))

