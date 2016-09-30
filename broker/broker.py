import socket
import argparse
from multiprocessing import Process, Pipe
from arduino import Arduino
from Queue import Queue, Empty
from nonblocking_pipe_listener import NonBlockingPipeListener as NBPL


# Socket params
host = 'localhost'
max_connections = 5


def server(port):
    # Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Reuse address/port
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_address = (host, port)

    print "Starting server on %s port %s" % server_address
    sock.bind(server_address)

    sock.listen(max_connections)

    while True:
        print "Waiting for clients..."
        client, address = sock.accept()
        data = client.recv(1024)

        if data:
            print "Received: %s" % data
            client.send(data)
            print "Sent %s to %s" % (data, address)

        client.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sensor manager')
    parser.add_argument('--port', action="store", dest="port", type=int, required=True)
    given_args = parser.parse_args()
    port = given_args.port

    parent, child = Pipe()

    # Starts the process
    arduino_proc = Arduino(child)
    arduino_proc.start()

    queue = Queue()

    # Creates a new thread that will be listening the pipe
    nbpl = NBPL(parent, queue)
    nbpl.setDaemon(True)
    nbpl.start()

    while True:
        try:
            received = queue.get(False)
        except Empty:
            pass
        else:
            # We got a message from the Arduino.
            print(received)


