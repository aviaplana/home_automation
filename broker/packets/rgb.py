import struct

from packet import Packet

'''
    RGBStrip payload structure:
    | r | g | b | is_on | reserved | instruction | ms_flick | t_dim |
    |   |   |   |  1 bit|    1 bit |      6 bits |          |       |
      1   1   1              1                       2         2      Bytes
'''


class RgbPacket(Packet):
    type = "rgb"

    def __init__(self):
        super(RgbPacket, self).__init__()
        self.id = 0
        self.instructions = {"set_all": 0, "set_defaults": 1,
                    "turn_on": 2, "turn_off": 3, "toggle": 4,
                    "change_color": 10, "change_blinking": 11,
                    "get_current": 20, "get_defaults": 21,
                    "error": 63
                    }

        self.r = 0
        self.g = 0
        self.b = 0
        self.is_on = 0
        self.instruction = 0
        self.ms_flick = 0
        self.t_dim = 0
        self.type = RgbPacket.type

    def interpret(self, received_buffer):
        values = struct.unpack("=5B2H", bytearray(received_buffer))
        ins = values[4] & 0x3F

        if ins not in self.instructions.values():
            return None

        self.instruction = ins

        # 20 - Current status of the strip
        # 21 - Default values stored in the EEPROM
        if self.instruction in [self.instructions["get_current"], self.instructions["get_defaults"]]:
            self.is_on = values[4] & 0x80
            self.id = values[0]
            self.r = values[1]
            self.g = values[2]
            self.b = values[3]
            self.ms_flick = values[5]
            self.t_dim = values[6]

        # ERROR
        elif self.instruction == self.instructions["error"]:
            self.id = values[0]

    def get_values(self):
        if self.instruction in [self.instructions["get_current"], self.instructions["get_defaults"]]:
            return {"id": self.id, "r": self.r, "g": self.g, "b": self.b, "is_on": self.is_on,
                    "ms_flick": self.ms_flick, "t_dim": self.t_dim,
                    "instruction": self.instructions.keys()[self.instructions.values().index(self.instruction)]}
        else:
            return {"id": self.id,
                    "instruction": self.instructions.keys()[self.instructions.values().index(self.instruction)]}

    @staticmethod
    def create_buffer(n_id,  values):
        if "instruction" not in values:
            print("Instruction must be specified")
            return None

        elif not n_id:
            print("Id must be specified")
            return None

        elif values["instruction"] not in self.instructions:
            print("ERROR: unknown instruction: " + values["instruction"])
            return None

        if values["instruction"] in ["set_all", "set_defaults"]:
            if not all(val in values for val in ("r", "g", "b", "ms_flick", "t_dim")):
                print("Not enough arguments")
                return None

        elif values["instruction"] in ["turn_on", "turn_off", "toggle", "get_current", "get_defaults"]:
            values["r"] = 0
            values["g"] = 0
            values["b"] = 0
            values["ms_flick"] = 0
            values["t_dim"] = 0

        elif values["instruction"] == "change_color":
            if not all(val in values for val in ("r", "g", "b")):
                print("Not enough arguments")
                return None

            else:
                if "t_dim" not in values:
                    values["t_dim"] = 0

                values["ms_flick"] = 0

        elif values["instruction"] == "change_blinking":
            if "ms_flick" not in values:
                print("Not enough arguments")
                return None
            else:
                values["r"] = 0
                values["g"] = 0
                values["b"] = 0
                values["t_dim"] = 0

        # \B | destination_id | payload | \E
        return struct.pack("=8B2H2B", ord("\\"), ord("B"), Packet.packet_types[RgbPacket.type], n_id, values["r"],
                           values["g"], values["b"], Packet.instructions[values["instruction"]],
                           values["ms_flick"], values["t_dim"], ord("\\"), ord("E"))

    def get_buffer(self):
        # \B | destination_id | payload | \E
        return struct.pack("=8B2H2B", ord("\\"), ord("B"), Packet.packet_types[RgbPacket.type], self.id, self.r,
                           self.g, self.b, self.instruction,
                           self.ms_flick, self.t_dim, ord("\\"), ord("E"))
