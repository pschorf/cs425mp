import socket, time
games = []
LISTEN_PORT = 5555
LOGFILE_NAME = 'server.log'
logfile = 0

def listenForRequests():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((socket.gethostbyname(socket.gethostname()), LISTEN_PORT))
    sock.listen(100)
    log('SERVER LISTENING ON ' + str(sock.getsockname()))
    while 1:
        (client, client_addr) = sock.accept()
        respond(client, client_addr)

def respond(client, client_addr):
    global games
    if len(games) == 0:
        games.append((client_addr, 4))
        log( 'SENT NEWGAME TO ' + str(client_addr))
        client.send('NEWGAME')
    else:
        (addr, count) = games[0]
        if count == 1:
            games.remove((addr, count))
        else:
            games[0] = (addr, count - 1)
        log('SENT JOIN ' + str(addr) + ' TO ' + str(client_addr))
        client.send('JOIN ' + str(addr))

def log(s):
    global logfile
    logfile.write('[' + time.asctime() + '] ' + s + '\r\n')
    logfile.flush()

logfile = open(LOGFILE_NAME, 'a')
listenForRequests()

