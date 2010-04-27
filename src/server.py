## @package server
# Defines the server
# @author Paul Schorfheide

import socket, time, re, threading, sys
## @var games
# The list of games waiting for players
games = []
## @var LISTEN_PORT
# The port to listen on
LISTEN_PORT = 5555
## @var LOGFILE_NAME
# The name of the file to log messages to
LOGFILE_NAME = 'server.log'
## @var TIMEOUT
# The number of seconds to keep games in the queue
TIMEOUT = 10
## @var logfile
# The logfile handle
logfile = 0

## the listener
def listenForRequests():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((socket.gethostbyname(socket.gethostname()), LISTEN_PORT))
    sock.listen(1000)
    log('SERVER LISTENING ON ' + str(sock.getsockname()))
    while 1:
        try:
            (client, client_addr) = sock.accept()
            req = parseRequest(client.recv(1024), client, client_addr)
        except:
            pass

## handle join requests from client
# @param client the client socket
# @param client_addr the address of the client socket
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

## increment the player waiting count for a game
#@param client the client socket
#@param client_addr the address of the client
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

## start a timer to cancel a game
#@param game the game to wait on
#@param create whether or not to create a timer if one does not exist
def makeTimer(game, create=False):
    global timers
    if game in timers:
        timers[game].cancel()
    if game in timers or create:
        timers[game] = threading.Timer(TIMEOUT, clearGame, [game])
        timers[game].daemon = True
        timers[game].start()

## parse a message from a client
#@param s the message
#@param client the client socket
#@param client_addr the address of the client socket
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

## change the leader of a game
#@param old the old leader
#@param new the new leader
def changeLeader(old, new):
    global games
    entry = [(a,b) for (a,b) in games if a == old]
    if len(entry) > 0:
        i = games.index(entry[0])
        games[i] = (new, entry[0][1])
    
## remove a game
#@param game the game to remove
def clearGame(game):
    global games
    i = [(a,b) for (a,b) in games if a == game]
    if len(i) > 0:
        games.remove(i[0])
    log('removed game ' + str(game))

## send a message and log the send event
#@param client the socket to send to
#@param client_addr the address to send to
#@param msg the message to send
def logAndSend(client, client_addr, msg):
    log('SENT ' + msg + ' TO '+ str(client_addr))
    client.send(msg)

## log a message
#@param s the message to log
def log(s):
    global logfile
    logfile.write('[' + time.asctime() + '] ' + s + '\r\n')
    logfile.flush()

## parse an address from a message
#@param s the string to parse
def parseAddr(s):
    m = re.search('\(\'([\d\.]+)\', (\d+)\)', s)
    return (m.group(1), int(m.group(2)))

## @cond RUN_FROM_COMMAND_LINE
if len(sys.argv) >= 2:
    port = int(sys.argv[1])
timers = {}
logfile = open(LOGFILE_NAME, 'a')
t = threading.Thread(target=listenForRequests())
t.start()

## @endcond

