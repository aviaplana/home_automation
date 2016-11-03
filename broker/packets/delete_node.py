import struct

from packet import Packet

'''
    Payload structure:

    | ID node |
    |    1    |

'''


class DeleteNodePacket(Packet):
    id_main_node = 1
    type = "delete_node"

    def __init__(self):
        super(AddNodePacket, self).__init__()
        self.id = 0
        self.type = DeleteNodePacket.type

    def get_values(self):
        return {"id": self.id, "pipe": self.id}

    def get_buffer(self):
        return struct.pack("=7B", ord("\\"), ord("B"), Packet.packet_types[DeleteNodePacket.type], DeleteNodePacket.id_main_node,
                           self.id, ord("\\"), ord("E"))

    @staticmethod
    def create_buffer(data):
        return struct.pack("=7B", ord("\\"), ord("B"), Packet.packet_types[DeleteNodePacket.type], DeleteNodePacket.id_main_node,
                           data["id"], ord("\\"), ord("E"))
