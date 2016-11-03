# Main process. Keeps track of the communications among socket and Arduino. It also manages the database.

import argparse
import random
import time
from pymongo import MongoClient
from multiprocessing import Pipe
from arduino import Arduino
from socket_server import SocketServer
from Queue import Queue, Empty
from nonblocking_pipe_listener import NonBlockingPipeListener as NBPL
from collections import deque

sock_node = {}  # id_node: socket
nodes = {}      # id_node: {type, pipe}
nodes_to_initialize = deque()
callbacks_confirmed = {}

arduino_pipe = None
socket_pipe = None

# Database parameters
db = None
db_host = "localhost"
db_port = 27017
db_user = ""
db_password = ""


def process_arduino(packet):
    global nodes
    global callbacks_confirmed

    if packet.type == "init_request":
        print "Starting initialization process. Hash %s, node type %s " % (packet.hash, packet.node_type)
        # ping all the nodes of the same type
        # if any of those doesn't reply, assign the pipe to the new one.
        can_initialize = True

        for st_id, st_node in nodes.items():
            if st_node["type"] == packet.node_type:
                can_initialize = False
                break

        # If there's no other node of the same kind, initialize
        if can_initialize:
            send_init(packet.node_type, packet.hash)

        else:
            nodes_to_initialize.append({"hash": packet.hash, "type": packet.node_type})

            # If there's no other node in the initialization queue, start the process
            if len(nodes_to_initialize) == 1:
                initialize_next_queue()

    elif packet.type == "rgb":
        if sock_node[packet.id]:
            client = sock_node[packet.id]
            arduino_pipe.send((client, data))

        else:
            print "Received %s packet %s" % (packet.type, packet.status)

    elif packet.type == "confirmation":
        if len(nodes_to_initialize) > 0:
            node_ini = nodes_to_initialize[0]

            if packet.id in node_ini["to_ping"]:
                if packet.status == 1:
                    print "Positive confirmation received from %s" % packet.id
                    node_ini["to_ping"].remove(packet.id)

                    if len(node_ini["to_ping"]) == 0:
                        send_init(node_ini["type"], node_ini["hash"])

                # We didn't get a response from the node, so we assume that it is down.
                else:
                    print "Negative confirmation received from %s" % packet.id

                    send_delete(packet.id)
                    callbacks_confirmed[packet.id] = {"function": callback_delete,
                                                      "params": {"type": node_ini["type"],
                                                                 "id": packet.id,
                                                                 "hash": node_ini["hash"]
                                                                 }
                                                      }

        elif packet.id in callbacks_confirmed:
            callbacks_confirmed[packet.id]["params"]["confirmation"] = packet.status
            callbacks_confirmed[packet.id]["function"](callbacks_confirmed[packet.id]["params"])

        else:
            print "Got confirmation from %s, status %s" % (packet.id, packet.status)


# Starts the initialization process for the next node in the queue. Pings all the nodes of the same type.
def initialize_next_queue():
    if len(nodes_to_initialize) > 0:
        nodes_ping = [id_node for (id_node, st_node) in nodes.items() if st_node["type"] == nodes_to_initialize[0]["type"]]

        nodes_to_initialize[0]["to_ping"] = nodes_ping

        print "Sending ping to ", nodes_ping
        p_to_send = {"type": "ping"}

        for ping_n in nodes_ping:
            p_to_send["id"] = ping_n
            arduino_pipe.send(p_to_send)


def send_delete(n_id):
    arduino_pipe.send({"type": "delete_node", "values": {"id": n_id}})

    try:
        del nodes[n_id]
        del sock_node[n_id]
    except KeyError:
        print "Couldn't delete node %s" % n_id
        pass


def send_init(n_type, n_hash, n_id=None):
    if not n_id:
        n_id = generate_id()

    n_pipe = generate_pipe()
    nodes[n_id] = {"type": n_type, "pipe": n_pipe}
    arduino_pipe.send({"type": "init_response", "id": n_id,
                       "values": {"hash": n_hash, "pipe": n_pipe}})

    print "Node initialized with id %s and pipe %s" % (n_id, n_pipe)

    callbacks_confirmed[n_id] = {"function": callback_init, "params": {"id": n_id, "pipe": n_pipe, "hash": n_hash}}


def callback_init(params):
    # TODO: What if confirmation is negative?
    if params["confirmed"]:
        arduino_pipe.send({"type": "add_node", "values": {"id": params["id"], "pipe": params["pipe"]}})
        nodes_to_initialize.popleft()
        initialize_next_queue()


def callback_delete(params):
    # TODO: What if confirmation is negative?
    if params["confirmed"]:
        send_init(params["type"], params["hash"], params["id"])


def generate_pipe():
    not_valid = True

    while not_valid:
        new_pipe = random.randint(162, 175)  # A2 - AF

        for n_id, node_t in nodes.items():
            if node_t['pipe'] == new_pipe:
                continue
        not_valid = False

    return new_pipe


def generate_id():
    for i in range(2, 256):
        if i not in nodes.keys():
            return i


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
    client = MongoClient(db_host, db_port)  # , db_user, db_password)
    global db
    db = client['home_automation']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sensor manager')
    parser.add_argument('--port', action="store", dest="port", type=int, required=True)
    given_args = parser.parse_args()
    port = given_args.port

    arduino_pipe, queue_arduino = init_arduino()
    socket_pipe, queue_socket = init_socket()
    init_database()

    while True:
        try:
            received = queue_arduino.get(False)
        except Empty:
            pass
        else:
            # We got a message from the Arduino.
            print "Received from id %s packet type %s" % (received.id, received.type)

            process_arduino(received)

        try:
            address, data = queue_socket.get(False)
        except Empty:
            pass
        else:
            print(data)

            sock_node[data["id"]] = address

            # We got a message from the Socket.
            print("Received from client ")
            print(sock_node)

        time.sleep(0.001) # Reduce CPU consumption