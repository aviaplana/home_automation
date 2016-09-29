import socket
import argparse


#Socket params
host = 'localhost'
max_connections = 5

def server(port):
    #Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #Reuse address/port
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_address = (host, port)

    print "Starting server on %s port %s" % server_address
    sock.bind(server_address)

    sock.listen(max_connections)

    while True:
        print "Waiting for clients..."
        client, address = sock.accept()
        data = client.recv(data_payload)

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
    server(port)

