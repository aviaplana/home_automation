import struct


class Packet(object):

    def __init__(self):
        self.id = 0

    @staticmethod
    def interpret_response(self, buffer):
        id, status = struct.unpack("=2B", bytearray(buffer))


