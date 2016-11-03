import struct

from packet import Packet

'''
    Payload structure:

    | Hash | Node type |
    |   2  |      1    |

'''


class InitRequestPacket(Packet):
    type = "init_request"

    def __init__(self):
        super(InitRequestPacket, self).__init__()
        self.id = 0
        self.hash = 0
        self.node_type = 0
        self.type = InitRequestPacket.type

    def interpret(self, received_buffer):
        values = struct.unpack("=1B1H1B", bytearray(received_buffer))
        self.id = values[0]
        self.hash = values[1]
        self.node_type = Packet.get_type_from_value(values[2])

    def get_values(self):
        return {"id": self.id, "hash": self.hash, "type": Packet.packet_types[self.node_type]}

    def get_buffer(self):
        # \B | destination_id | payload | \E
        return struct.pack("=3B1H3B", ord("\\"), ord("B"), Packet.packet_types[InitRequestPacket.type], self.id, self.hash,
                           Packet.packet_types[self.node_type], ord("\\"), ord("E"))
