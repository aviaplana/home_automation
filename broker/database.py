import pymongo


class Database:
    connection = ""

    def __init__(self):
        self.database = ""
        self.host = "localhost"
        self.port = "27017"
        self.user = ""
        self.password = ""
        self.connect()

    def connect(self):
        self.connection = pymongo.MongoClient(self.host, self.port)

