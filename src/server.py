import socket, time, re, threading, sys
games = []
LISTEN_PORT = 5555
LOGFILE_NAME = 'server.log'
TIMEOUT = 10

logfile = 0

def listenForRequests():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((socket.gethostbyname(socket.gethostname()), LISTEN_PORT))
    sock.listen(100)
    log('SERVER LISTENING ON ' + str(sock.getsockname()))
    while 1:
        (client, client_addr) = sock.accept()
        req = parseRequest(client.recv(1024), client, client_addr)

def joinGame(client, client_addr):
    global games
    if len(games) == 0:
        games.append((client_addr, 4))
        logAndSend(client, client_addr, 'NEWGAME')
        makeTimer(client_addr, True)
    else:
        (addr, count) = games[0]
        if count == 1:
            games.remove((addr, count))
        else:
            games[0] = (addr, count - 1)
        logAndSend(client, client_addr, 'JOIN ' + str(addr))

def addPlayer(client, client_addr):
    global games
    entry = [(a,b) for (a,b) in games if a == client_addr]
    if len(entry) > 0:
        i = games.index(entry[0])
        if games[i][1] < 4:
            games[i] = (games[i][0], games[i][1] + 1)
        else:
            logAndSend(client, client_addr, 'ERROR: TOO MANY PLAYERS')
            return
    else:
        makeTimer(client_addr, True)
        games.append((client_addr, 1))
    logAndSend(client, client_addr, 'REQUEST PENDING')

def makeTimer(game, create=False):
    global timers
    if game in timers:
        timers[game].cancel()
    if game in timers or create:
        timers[game] = threading.Timer(TIMEOUT, clearGame, [game])
        timers[game].daemon = True
        timers[game].start()

def parseRequest(s, client, client_addr):
    global timers
    arr = s.split('###')
    if len(arr) < 2:
        return
    else:
        s = arr[1]
        source_addr = parseAddr(arr[0])
    log('Received ' + s + ' from ' + str(client_addr))
    makeTimer(source_addr)
    if s.find('JOIN') > -1:
        joinGame(client, client_addr)
    elif s.find('ADDPLAYER') > -1:
        addPlayer(client, source_addr)
    elif s.find('PING') > -1:
        pass
    elif s.find('LEADER-CHANGE') > -1:
        arr = s.split('##')
        if len(s) < 3:
            return
        else:
            changeLeader(parseAddr(arr[1]), parseAddr(arr[2]))
    else:
        logAndSend(client, client_addr, 'ERROR: PARSE ERROR')

def changeLeader(old, new):
    global games
    entry = [(a,b) for (a,b) in games if a == old]
    if len(entry) > 0:
        i = games.index(entry[0])
        games[i] = (new, entry[0][1])
    

def clearGame(game):
    global games
    i = [(a,b) for (a,b) in games if a == game]
    if len(i) > 0:
        games.remove(i[0])
    log('removed game ' + str(game))
def logAndSend(client, client_addr, msg):
    log('SENT ' + msg + ' TO '+ str(client_addr))
    client.send(msg)
    
def log(s):
    global logfile
    logfile.write('[' + time.asctime() + '] ' + s + '\r\n')
    logfile.flush()
    
def parseAddr(s):
    m = re.search('\(\'([\d\.]+)\', (\d+)\)', s)
    return (m.group(1), int(m.group(2)))

    
if len(sys.argv) >= 2:
    port = int(sys.argv[1])
timers = {}
logfile = open(LOGFILE_NAME, 'a')
t = threading.Thread(target=listenForRequests())
t.start()

