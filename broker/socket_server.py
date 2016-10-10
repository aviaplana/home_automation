from multiprocessing import Process
from Queue import Queue, Empty
from nonblocking_socket_listener import NonBlockingSocketListener as NBSL
from nonblocking_pipe_listener import NonBlockingPipeListener as NBPL
import socket
import time
import json


class SocketServer(Process):

    def __init__(self, port, pipe):
        Process.__init__(self)
        self.socket = ""
        self.sockets = {}
        self.port = port
        self.pipe = pipe

    def process_received(self, pkt):
        if pkt["instruction"] == "get_instructions":
            return
        print pkt

    def run(self):
        # Socket params
        host = 'localhost'
        max_connections = 5
        queue_socket = Queue()
        queue_pipe = Queue()

        # Create socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Reuse address/port
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_address = (host, self.port)

        print "Starting server on %s port %s" % server_address
        self.socket.bind(server_address)

        self.socket.listen(max_connections)

        # New thread that will listen the socket
        nbsl = NBSL(self.socket, queue_socket)
        nbsl.setDaemon(True)
        nbsl.start()

        # New thread that will listen the pipe
        nbpl = NBPL(self.pipe, queue_pipe)
        nbpl.setDaemon(True)
        nbpl.start()

        while True:
            # Checks for socket clients
            try:
                received = queue_socket.get(False)
            except Empty:
                pass
            else:
                address, connection, data = received

                self.sockets[address] = connection
                self.process_received(data)
                self.pipe.send((address, data))

            # Checks for messages from the main thread
            try:
                received = queue_pipe.get(False)
            except Empty:
                pass
            else:
                client, data = received
                socket_c = self.sockets[client]

                if client in self.sockets:
                    if socket_c.send(json.dumps(data)):
                        print "Sent response to client", data
                    else:
                        print "Error while sending data to ", client
                else:
                    print "No socket found for", client

                #self.process_received(received)

            time.sleep(0.001) # Reduce CPU consumption

