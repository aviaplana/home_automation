import argparse
import time
from multiprocessing import Pipe
from arduino import Arduino
from socket_server import SocketServer
from Queue import Queue, Empty
from nonblocking_pipe_listener import NonBlockingPipeListener as NBPL

sock_node = {}  # id node, socket

def process_arduino(data, pipe):
    if data["instruction"] == "confirmation":
        client = sock_node[data["id"]].pop()
        pipe.send((client, data))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sensor manager')
    parser.add_argument('--port', action="store", dest="port", type=int, required=True)
    given_args = parser.parse_args()
    port = given_args.port

    # Arduino process
    arduino_parent_pipe, arduino_child_pipe = Pipe()

    # Starts the process
    arduino_proc = Arduino(arduino_child_pipe)
    arduino_proc.start()

    queue_arduino = Queue()

    # Creates a new thread that will be listening the pipe
    nbpl_arduino = NBPL(arduino_parent_pipe, queue_arduino)
    nbpl_arduino.setDaemon(True)
    nbpl_arduino.start()

    # Socket process
    socket_parent_pipe, socket_child_pipe = Pipe()

    # Starts the process
    socket_proc = SocketServer(port, socket_child_pipe)
    socket_proc.start()

    queue_socket = Queue()

    # Creates a new thread that will be listening the pipe
    nbpl_socket = NBPL(socket_parent_pipe, queue_socket)
    nbpl_socket.setDaemon(True)
    nbpl_socket.start()

    while True:
        try:
            received = queue_arduino.get(False)
        except Empty:
            pass
        else:
            # We got a message from the Arduino.
            print("Received from Arduino: " + str(received["id"]))

            process_arduino(received, socket_parent_pipe)
            print(received)

        try:
            address, data = queue_socket.get(False)
        except Empty:
            pass
        else:
            print(data)
            if data["id"] not in sock_node:
                sock_node[data["id"]] = Queue()

            sock_node[data["id"]].put(address)

            # We got a message from the Socket.
            print("Received from client ")
            print(sock_node)

        time.sleep(0.001) # Reduce CPU consumption