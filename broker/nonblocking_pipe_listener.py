from threading import Thread


# This thread just listens for messages from the pipe. If it receives a new one, it puts it in the queue.
class NonBlockingPipeListener(Thread):

    def __init__(self, pipe, queue):
        Thread.__init__(self)
        self.pipe = pipe
        self.queue = queue

    def run(self):
        while True:
            line = self.pipe.recv()
            if line:
                self.queue.put(line)
