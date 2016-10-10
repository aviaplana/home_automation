import struct


class Packet(object):

    def __init__(self):
        self.id = 0
        self.instructions = {}

    @staticmethod
    def interpret_response(self, buffer):
        id, status = struct.unpack("=2B", bytearray(buffer))

    def get_values(self):
        return {"id": self.id, "instruction": "confirmation", "success": self.status}

    def get_instructions(self):
        return [instruction for instruction, val in self.instructions]
