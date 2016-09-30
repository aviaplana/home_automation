from threading import Thread


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
