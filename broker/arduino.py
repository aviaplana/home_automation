import time
from multiprocessing import Process

import serial
from Queue import Queue, Empty

from nonblocking_pipe_listener import NonBlockingPipeListener as NBPL
from packets.packet import Packet
from packets.rgb import RgbPacket
from packets.init_request import InitRequestPacket
from packets.init_response import InitResponsePacket
from packets.confirmation import ConfirmationPacket
from packets.add_node import AddNodePacket
from packets.delete_node import DeleteNodePacket

class Arduino(Process):

    def __init__(self, pipe):
        Process.__init__(self)
        self.ser = ""
        self.pipe = pipe

    '''
    Reads the serial port, and returns the received packet.
    '''
    def read_data(self):
        pos = 0
        type_pkt = 0
        buff = bytearray()
        prev = 0
        max_size = 35

        if self.ser.inWaiting() <= 0:
            return None

        while True:
            c = self.ser.read()
            if pos == 0 and c != '\\':
                return None
            elif pos == 1 and c != 'B':
                return None
            elif pos == 2:
                type_pkt = int(c.encode('hex'), 16)
            elif pos > 2:
                if c == '\\':
                    prev = pos
                elif (pos - 1) == prev and c == 'E':
                    return {"type": type_pkt, "payload": buff}
                elif pos > max_size:
                    return None
                else:
                    buff.append(c)

            pos += 1

    @staticmethod
    def decode_packet(packet):
        if packet["type"] == Packet.packet_types["confirmation"]:
            confirmation_packet = ConfirmationPacket()
            confirmation_packet.interpret_response(packet["payload"])
            return confirmation_packet

        elif packet["type"] == Packet.packet_types["rgb"]:
            rgb_packet = RgbPacket()
            rgb_packet.interpret(packet["payload"])
            return rgb_packet

        elif packet["type"] == Packet.packet_types["init_request"]:
            init_req_packet = InitRequestPacket()
            init_req_packet.interpret(packet["payload"])
            return init_req_packet

        else:
            return None

    @staticmethod
    def build_error(node_id, error_msg):
        return {"id": node_id, "instruction": "error", "message": error_msg}

    '''
    This function processes the information received by the pipe.
    '''
    def process_received(self, received):
        if "type" not in received.keys():
            return None

        packet = self.prepare_packet(received)

        # for a in packet:
        #    print hex(ord(a))

        if packet is None:
            return None

        if self.ser.isOpen():
            self.ser.write(packet)
            return True

        else:
            print "ERROR: Serial port not opened"
            return None

    @staticmethod
    def prepare_packet(values):
        if values["type"] == "rgb":
            if "values" not in values.keys():
                return None
            return RgbPacket.create_buffer(values["values"])

        elif values["type"] == "ping":
            return Packet.create_buffer_ping(values["id"])

        elif values["type"] == "init_response":
            if "values" not in values.keys():
                return None
            return InitResponsePacket.create_buffer(values["id"], values["values"])

        elif values["type"] == "add_node":
            if "values" not in values.keys():
                return None
            return AddNodePacket.create_buffer(values["values"])

        elif values["type"] == "delete_node":
            if "values" not in values.keys():
                return None
            return DeleteNodePacket.create_buffer(values["values"])

        return None

    '''
    Method called when the process is started
    '''
    def run(self):
        port = '/dev/tty.wchusbserial1d1110'
        baud = 9600
        self.ser = serial.Serial(port, baud)
        queue = Queue()

        # New thread that will listen the pipe
        nbpl = NBPL(self.pipe, queue)
        nbpl.setDaemon(True)
        nbpl.start()

        print("Starting arduino...")
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

        while True:
            packet = self.read_data()

            if packet:
                decoded = self.decode_packet(packet)
                self.pipe.send(decoded) # id, packet

            try:
                received = queue.get(False)
            except Empty:
                pass
            else:
                self.process_received(received)

            time.sleep(0.001) # Reduce CPU consumption
