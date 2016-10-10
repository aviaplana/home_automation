from threading import Thread
import json


# This thread just listens for messages from the pipe. If it receives a new one, it puts it in the queue.
class NonBlockingSocketListener(Thread):

    def __init__(self, socket, queue):
        Thread.__init__(self)
        self.socket = socket
        self.queue = queue

    def run(self):
        while True:
            conn, address = self.socket.accept()
            data = conn.recv(1024)
            if data:
                #print "Received: %s" % data
                json_data = json.loads(data)
                self.queue.put((address, conn, json_data))
