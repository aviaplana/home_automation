import struct

from packet import Packet

'''
    Payload structure:

    | ID node | Pipe |
    |    1    |   1  |

'''


class AddNodePacket(Packet):
    id_main_node = 1
    type = "add_node"

    def __init__(self):
        super(AddNodePacket, self).__init__()
        self.id = 0
        self.pipe = 0
        self.type = AddNodePacket.type

    def get_values(self):
        return {"id": self.id, "pipe": self.id}

    def get_buffer(self):
        return struct.pack("=8B", ord("\\"), ord("B"), Packet.packet_types[AddNodePacket.type],
                           AddNodePacket.id_main_node, self.id, self.pipe, ord("\\"), ord("E"))

    @staticmethod
    def create_buffer(data):
        keys = data.keys()
        if "id" not in keys or "pipe" not in keys:
            return None

        return struct.pack("=8B", ord("\\"), ord("B"), Packet.packet_types[AddNodePacket.type],
                           AddNodePacket.id_main_node, data["id"], data["pipe"], ord("\\"), ord("E"))
