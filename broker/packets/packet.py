import struct


class Packet(object):
    packet_types = {"ping": 0, "confirmation": 1, "init_request": 2, "init_response": 3,
                    "add_node": 10, "delete_node": 11, "delete_list": 12,
                    "rgb": 20}

    def __init__(self):
        self.id = 0
        self.type = 0
        self.instructions = {}

    def get_instructions(self):
        return [instruction for instruction, val in self.instructions]

    @staticmethod
    def create_buffer_ping(n_id):
        return Packet.create_buffer(n_id, "ping")

    @staticmethod
    def create_buffer(n_id, n_type):
        if n_type in Packet.packet_types:
            return struct.pack("=6B", ord("\\"), ord("B"), Packet.packet_types[n_type], n_id, ord("\\"), ord("E"))
        else:
            return None

    @staticmethod
    def get_type_from_value(val):
        for n_type, value in Packet.packet_types.iteritems():
            if value == val:
                return n_type

    def get_buffer(self):
        if self.type in Packet.packet_types:
            return struct.pack("=6B", ord("\\"), ord("B"), self.type, self.id, ord("\\"), ord("E"))
        else:
            return None
