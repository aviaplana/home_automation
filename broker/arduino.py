import serial
from packet import Packet
from rgb_packet import RgbPacket
from multiprocessing import Process
from interruptingcow import timeout


class Arduino(Process):

    def __init__(self, receive_pipe, send_pipe):
        Process.__init__(self)
        self.ser = ""
        self.receive_pipe = receive_pipe
        self.send_pipe = send_pipe

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
                    return
                else:
                    buff.append(c)

            pos += 1

    @staticmethod
    def decode_packet(packet):
        # TODO:  Should specify which kind of packet we are returning
        if packet["type"] == 1:
            return Packet.interpret_response(packet["payload"])

        elif packet["type"] == 10:
            rgb_packet = RgbPacket()
            rgb_packet.interpret(packet["payload"])
            return rgb_packet

        else:
            return None

    # received structure: (id, action, [values])
    def process_received(self, received):
        id_node = received[0]
        action = received[1]

        # TODO: Should track which kind of node is each one. Should have a table with id - type, for instance id 1 -> type rgb
        if id_node == 1:
            if action == "send":
                if received[3]:
                    result = RgbPacket.create_buffer(received[3])

                    if result is None:
                        return None

                    elif self.ser.isOpen():
                        # This tells us if we have to expect a response from the node
                        will_reply = result[0]
                        self.ser.write(result[1])

                        try:
                            with timeout(0.05, exception=RuntimeError):
                                # Waits for confirmation
                                while True:
                                    packet = self.read_data()
                                    if packet:
                                        response = self.decode_packet(packet)
                                        break
                        except RuntimeError:
                            print("Response timed out")
                            self.send_pipe.send((id_node, "Confirmation timed out"))
                            return None

                        # TODO: Make sure that we have a confirmation packet
                        rec_id, rec_res = response

                        # let's get the response
                        if not will_reply:
                            self.send_pipe.send((id_node, "OK" if rec_res else "KO"))

                        else:
                            try:
                                with timeout(0.05, exception=RuntimeError):
                                    # Waits for the response
                                    while True:
                                        packet = self.read_data()
                                        if packet:
                                            response = self.decode_packet(packet)
                                            break
                            except RuntimeError:
                                print("Response timed out")
                                self.send_pipe.send((id_node, "Response timed out"))
                                return None

                            self.send_pipe()
                    else:
                        print("Serial not opened")
                else:
                    print("ERROR: No values to send")

    # Method called when the process is started
    def run(self):
        port = '/dev/tty.wchusbserial1d1120'
        baud = 9600
        self.ser = serial.Serial(port, baud)

        while True:
            packet = self.read_data()
            if packet:
                print "Received packet type " + str(packet["type"]) + ": "
                print self.decode_packet(packet)

            received = self.receive_pipe.recv()
            if received:
                self.process_received(received)


