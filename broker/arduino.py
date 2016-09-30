import serial
from Queue import Queue, Empty
from packet import Packet
from rgb_packet import RgbPacket
from multiprocessing import Process
from interruptingcow import timeout
from nonblocking_pipe_listener import NonBlockingPipeListener as NBPL


class Arduino(Process):

    def __init__(self, pipe):
        Process.__init__(self)
        self.ser = ""
        self.pipe = pipe
        self.pipe = pipe

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
                            self.pipe.send((id_node, "Confirmation timed out"))
                            return None

                        # TODO: Make sure that we have a confirmation packet
                        rec_id, rec_res = response

                        print("Got confirmation from " + str(rec_id) + ": " + str(rec_res))

                        # let's get the response
                        if not will_reply:
                            self.pipe.send((id_node, "OK" if rec_res else "KO"))

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
                                self.pipe.send((id_node, "Response timed out"))
                                return None

                            self.pipe()
                    else:
                        print("Serial not opened")
                else:
                    print("ERROR: No values to send")

    # Method called when the process is started
    def run(self):
        port = '/dev/tty.wchusbserial1d1120'
        baud = 9600
        self.ser = serial.Serial(port, baud)
        queue = Queue()

        # New thread that will listen the pipe
        nbpl = NBPL(self.pipe, queue)
        nbpl.setDaemon(True)
        nbpl.start()

        print("Starting arduino...")

        while True:
            packet = self.read_data()

            if packet:
                print "Received packet type " + str(packet["type"]) + ": "
                self.pipe.send(self.decode_packet(packet))

            try:
                received = queue.get(False)
            except Empty:
                pass
            else:
                print(received)
                self.process_received(received)