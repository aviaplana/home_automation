import struct

from packet import Packet

'''
    Payload structure:

    | Status |
    |    1   |

'''


class ConfirmationPacket(Packet):
    type = "confirmation"

    def __init__(self):
        super(ConfirmationPacket, self).__init__()
        self.id = 0
        self.type = ConfirmationPacket.type
        self.status = 0

    def interpret_response(self, buff):
        self.id, self.status = struct.unpack("=2B", bytearray(buff))

    def get_values(self):
        return {"id": self.id, "success": self.status}
