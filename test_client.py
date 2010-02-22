import socket

def openConnection():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((socket.gethostbyname(socket.gethostname()), 5555))
    return sock.recv(1024)


for i in range(0,6):
    print openConnection()
