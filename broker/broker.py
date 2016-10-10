# Main process. Keeps track of the communications among socket and Arduino. It also manages the database.

import argparse
import time
from pymongo import MongoClient
from multiprocessing import Pipe
from arduino import Arduino
from socket_server import SocketServer
from Queue import Queue, Empty
from nonblocking_pipe_listener import NonBlockingPipeListener as NBPL

sock_node = {}  # id_node: socket
nodes = {}      # id_node: type

# Database parameters
db = None
db_host = "localhost"
db_port = "27017"
db_user = ""
db_password = ""


def process_arduino(data, pipe):
    if data["instruction"] == "confirmation":
        # FIFO. Pops the oldest socket related to the node.
        client = sock_node[data["id"]].pop()
        pipe.send((client, data))


def init_arduino():
    # Arduino process
    parent_pipe, child_pipe = Pipe()

    # Starts the process
    proc = Arduino(child_pipe)
    proc.start()

    queue = Queue()

    # Creates a new thread that will be listening the pipe
    nbpl = NBPL(parent_pipe, queue)
    nbpl.setDaemon(True)
    nbpl.start()

    return parent_pipe, queue


def init_socket():
    # Socket process
    parent_pipe, child_pipe = Pipe()

    # Starts the process
    proc = SocketServer(port, child_pipe)
    proc.start()

    queue = Queue()

    # Creates a new thread that will be listening the pipe
    nbpl = NBPL(parent_pipe, queue)
    nbpl.setDaemon(True)
    nbpl.start()
    return parent_pipe, queue


def init_database():
    client = MongoClient(db_host, db_port, db_user, db_password)
    db = client.home_automation
    db.nodes.find("", {"id": 1, "type": 1})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sensor manager')
    parser.add_argument('--port', action="store", dest="port", type=int, required=True)
    given_args = parser.parse_args()
    port = given_args.port

    arduino_parent_pipe, queue_arduino = init_arduino()
    socket_parent_pipe, queue_socket = init_socket()
    # init_database()

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