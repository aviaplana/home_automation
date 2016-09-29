import serial
import struct

port = '/dev/tty.wchusbserial1410'
baud = 9600
ser = serial.Serial(port, baud)


def read_data():
    pos = 0
    type_pkt = 0
    buff = bytearray()
    prev = 0
    max_size = 35

    if ser.inWaiting() <= 0:
        return

    while True:
        c = ser.read()
        if pos == 0 and c != '\\':
            return
        elif pos == 1 and c != 'B':
            return
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



def decode_packet(packet):

    if packet["type"] == 10:
        '''
            RGBStrip payload structure:
            | id | r | g | b | is_on | reserved | instruction | ms_flick | t_dim |
            |    |   |   |   |  1 bit|    1 bit |      6 bits |          |       |
              1    1   1   1              1                       2         2      Bytes
        '''

        result = struct.unpack("=5B2H", bytearray(packet["payload"]))

        return result


while True:
    packet = read_data()
    if packet:
        print "Received packet type " + str(packet["type"]) + ": "
        print decode_packet(packet)
