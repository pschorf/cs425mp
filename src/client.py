## @package client
# Higher level client handling group management
# @author Paul Schorfheide

import socket, re, threading, matchmaker, time, os, sys
## @var NAMESERVER
# the default server name
NAMESERVER = socket.gethostbyname(socket.gethostname())
## @var NSPORT
# the default server port
NSPORT = 5555
## @var file_lock
# lock for the log file
file_lock = threading.Lock()
## @var TIMEOUT
# the default timeout interval
TIMEOUT = 90

## a higher level client handling group management
class client(object):
    ## connect to a new game
    #@return the other players in the game
    def findGame(self):
        x = self._matchmaker.findGame()
        self.log(str(self._matchmaker.getAddress()))
        return x
    
    ## disconnect from the current game
    def disconnect(self):
        self._matchmaker.disconnect()
    
    ## return the (ip, port) for this client
    #@return  the (ip, port) of this client  
    def getSelf(self):
        return self._matchmaker.getAddress()
    ## return the leader for this client
    #@return the (ip, port) of the leader
    def getLeader(self):
        return self._matchmaker.getLeader()
    ## return the other players in the game
    #@return a list of the other players in the game
    def getPlayers(self):
        return self._matchmaker.getPlayers()
    
    ## send a message to another player
    #@param target the client to send the message to
    #@param msg the message to send
    def send(self, target, msg):
        log = msg
        if msg.find('SYNC') > -1:
            log = 'SYNCNEWPLAYER'
        self.log('sent ' + log + ' to ' + str(target))
        self._matchmaker.send(target, msg)
    
    ## helper to send a message to all clients
    #@param msg the message to send
    def sendToAll(self, msg):
        for player in self.getPlayers():
            self.send(player, msg)
            
    ## message handler function
    #@param msg the message text
    #@param source the sender
    def _handleMsg(self, msg, source):
        if not source in self.getPlayers():
            return
        if source in self._timers:   
            self._timers[source].cancel()
        if source in self._lostPlayers:
            self._lostPlayers[source] = 0
        if self._isSafe:
            self._timers[source] = threading.Timer(TIMEOUT, self._search, [source])
            self._timers[source].daemon = True
            self._timers[source].start()
        log = msg
        if msg.find('SYNC') > -1:
            log = 'SYNCNEWPLAYER'
        self.log('received ' + log + ' from ' + str(source))
        if msg.find('LOST') > -1:
            self._handleLost(msg)
        elif msg.find('KICK') > -1 and source == self.getLeader():
            self._handleKick(msg)
        elif msg.find('LEADER-ELECT') > -1:
            self._handleElect(msg)
        elif self._msgHandler != None:
            self._msgHandler(msg, source)
    
    ## handler for election messages
    #@param msg the message text
    def _handleElect(self, msg):
        arr = msg.split('##')
        if len(arr) < 2:
            return
        leader = matchmaker.parseAddr(arr[1])
        if leader == self.getLeader():
            self._matchmaker.changeLeader()
            self.log('new leader: ' + str(self.getLeader()))
    
    ## handler for lost messages
    #@param msg the message text
    def _handleLost(self, msg):
        missing = matchmaker.parseAddr(msg)
        self._incrementPlayerLost(missing)

    ##handler for kick messages
    #@param msg the message text
    def _handleKick(self, msg):
        kicked = matchmaker.parseAddr(msg)
        if kicked == None:
            self._log("Failed to parse " + msg)
            return
        if kicked == self._matchmaker.getAddress():
            self.disconnect()
        else:
            self._matchmaker.removePlayer(kicked)
            
    ## increment the number of intervals a player has been missing for
    #@param missing the missing player
    def _incrementPlayerLost(self, missing):
        if missing in self._lostPlayers:
            self._lostPlayers[missing] = self._lostPlayers[missing] + 1
        else:
            self._lostPlayers[missing] = 1
        self.log(str(missing) + ' has count ' + str(self._lostPlayers[missing]))
        
    ## handler for player added event
    #@param player the added player  
    def _addPlayer(self, player):
        if player == None:
            raise Exception()
        if self._isSafe:
            self._timers[player] = threading.Timer(TIMEOUT, self._search, [player])
            self._timers[player].daemon = True
            self._timers[player].start()
        self.log('added ' + str(player))
        if self._playerAddedHander != None:
            self._playerAddedHander(player)
            
    ## handler for player removed event
    #@param player the removed player
    def _removePlayer(self, player):
        if player in self._timers:
            self._timers[player].cancel()
            del self._timers[player]
            self.log('removed ' + str(player))
            if self._playerRemovedHander != None:
                self._playerRemovedHander(player)
            
    ## called when a player is missing
    #@param player the missing player
    def _search(self, player):
        self._incrementPlayerLost(player)
        if self._matchmaker.getAddress() != self.getLeader():
            self.send(self.getLeader(), 'LOST ' + str(player))
        if self._isSafe:
            self._timers[player] = threading.Timer(TIMEOUT, self._search, [player])
            self._timers[player].daemon = True
            self._timers[player].start()
        if self.getLeader() == self._matchmaker.getAddress() and self._lostPlayers[player] > len(self.getPlayers())/2:
            del self._lostPlayers[player]
            for i in self.getPlayers():
                self.send(i, 'KICK ' + str(player))           
            self._matchmaker.removePlayer(player)
        if self._matchmaker.getLeader() in self._lostPlayers and self._lostPlayers[self._matchmaker.getLeader()] >= 2:
            self._electLeader()
            
    ## change leader 
    def _electLeader(self):
        for player in self.getPlayers():
            self.send(player, 'LEADER-ELECT##' + str(self.getLeader()))
        self._matchmaker.changeLeader()
        self.log('new leader: ' + str(self.getLeader()))
        
    ## constructor
    #@param servername the server ip
    #@param port the server port
    #@param onMessageReceived the message received handler
    #@param onPlayerAdded handler for player added
    #@param onPlayerRemoved handler for player removed
    #@param onLeaderChange handler for when the leader is changed
    #@param isSafe determines the number of listener threads to run        
    def __init__(self, servername=socket.gethostbyname(socket.gethostname()), 
                 port=5555,
                 onMessageReceived=None,
                 onPlayerAdded=None,
                 onPlayerRemoved=None,
                 onLeaderChange=None,
                 isSafe=True):
        self._matchmaker = matchmaker.matchmaker(servername=servername, port=port, handler=self._handleMsg,
                                                 onLeaderChanged=onLeaderChange)
        self._timers = {}
        self._matchmaker.onPlayerAdded = self._addPlayer
        self._matchmaker.onPlayerRemoved = self._removePlayer
        self._logFile = open(self._getLog(), 'w')
        self._lostPlayers = {}
        self._isSafe = isSafe
        if self._isSafe:
            t = threading.Timer(5,self._heartbeat)
            t.daemon = True
            t.start()
        self._msgHandler = onMessageReceived
        self._playerAddedHander = onPlayerAdded
        self._playerRemovedHander = onPlayerRemoved
    
    ## send a ping to all other players
    def _heartbeat(self):
        for player in self.getPlayers():
            self.send(player, 'ping')
        t = threading.Timer(5,self._heartbeat)
        t.daemon = True
        t.start()
    
    ## log a message to a file
    #@param msg the message to log
    def log(self, msg):
        self._logFile.write('[' + time.asctime() + '] ' + msg + '\n')
        self._logFile.flush()

    ## get a log file
    #@return the log file name
    def _getLog(self):
        file_lock.acquire()
        files = os.listdir('logs')
        curFile = 0
        for file in files:
            m = re.match(str(os.getpid()) + '_(\d+)\.log', file)
            if m != None:
                i = int(m.group(1))
                if i >= curFile:
                    curFile = i + 1
        file = 'logs/' + str(os.getpid()) + '_' + str(curFile) + '.log'
        f = open(file, 'w')
        f.close()
        file_lock.release()
        return file
## @cond RUN_FROM_COMMAND_LINE
def run():
    name = socket.gethostbyname(socket.gethostname())
    port = 5555
    if len(sys.argv) >= 2:
        name = sys.argv[1]
    if len(sys.argv) >= 3:
        port = int(sys.argv[2])
    c = client(name, port)
    c.findGame()
    time.sleep(60)
    c.disconnect()
if __name__ == '__main__':
    run()
## @endcond