import socket, re, threading, matchmaker, time, os, sys

NAMESERVER = socket.gethostbyname(socket.gethostname())
NSPORT = 5555
file_lock = threading.Lock()
TIMEOUT = 10


class client(object):
    def findGame(self):
        x = self._matchmaker.findGame()
        self.log(str(self._matchmaker.getAddress()))
        return x
    def disconnect(self):
        self._matchmaker.disconnect()
    def getSelf(self):
        return self._matchmaker.getAddress()
    def getLeader(self):
        return self._matchmaker.getLeader()
    def getPlayers(self):
        return self._matchmaker.getPlayers()
    def send(self, target, msg):
        self.log('sent ' + msg + ' to ' + str(target))
        self._matchmaker.send(target, msg)
    def sendToAll(self, msg):
        for player in self.getPlayers():
            self.send(player, msg)
    def _handleMsg(self, msg, source):
        if not source in self.getPlayers():
            return
        if source in self._timers:   
            self._timers[source].cancel()
        if source in self._lostPlayers:
            self._lostPlayers[source] = 0
        self._timers[source] = threading.Timer(TIMEOUT, self._search, [source])
        self._timers[source].daemon = True
        self._timers[source].start()
        self.log('received ' + msg + ' from ' + str(source))
        if msg.find('LOST') > -1:
            self._handleLost(msg)
        elif msg.find('KICK') > -1 and source == self.getLeader():
            self._handleKick(msg)
        elif msg.find('LEADER-ELECT') > -1:
            self._handleElect(msg)
        if self._msgHandler != None:
            self._msgHandler(msg, source)
            
    def _handleElect(self, msg):
        arr = msg.split('##')
        if len(arr) < 2:
            return
        leader = matchmaker.parseAddr(arr[1])
        if leader == self.getLeader():
            self._matchmaker.changeLeader()
            self.log('new leader: ' + str(self.getLeader()))
                    
    def _handleLost(self, msg):
        missing = matchmaker.parseAddr(msg)
        self._incrementPlayerLost(missing)

    def _handleKick(self, msg):
        kicked = matchmaker.parseAddr(msg)
        if kicked == self._matchmaker.getAddress():
            self.disconnect()
        else:
            self._matchmaker.removePlayer(kicked)
            
    def _incrementPlayerLost(self, missing):
        if missing in self._lostPlayers:
            self._lostPlayers[missing] = self._lostPlayers[missing] + 1
        else:
            self._lostPlayers[missing] = 1
        self.log(str(missing) + ' has count ' + str(self._lostPlayers[missing]))  
    def _addPlayer(self, player):
        self._timers[player] = threading.Timer(TIMEOUT, self._search, [player])
        self._timers[player].daemon = True
        self._timers[player].start()
        self.log('added ' + str(player))
        if self._playerAddedHander != None:
            self._playerAddedHander(player)
    def _removePlayer(self, player):
        if player in self._timers:
            self._timers[player].cancel()
            del self._timers[player]
            self.log('removed ' + str(player))
            if self._playerRemovedHander != None:
                self._playerRemovedHander(player)
            
    def _search(self, player):
        self._incrementPlayerLost(player)
        if self._matchmaker.getAddress() != self.getLeader():
            self.send(self.getLeader(), 'LOST ' + str(player))
        self._timers[player] = threading.Timer(TIMEOUT, self._search, [player])
        self._timers[player].daemon = True
        self._timers[player].start()
        if self.getLeader() == self._matchmaker.getAddress() and self._lostPlayers[player] > len(self.getPlayers())/2:
            del self._lostPlayers[player]
            for i in self.getPlayers():
                self.send(i, 'KICK ' + str(player))           
            self._matchmaker.removePlayer(player)
            self._matchmaker.requestNewPlayer()
        if self._matchmaker.getLeader() in self._lostPlayers and self._lostPlayers[self._matchmaker.getLeader()] >= 2:
            self._electLeader()
    def _electLeader(self):
        for player in self.getPlayers():
            self.send(player, 'LEADER-ELECT##' + str(self.getLeader()))
        self._matchmaker.changeLeader()
        self.log('new leader: ' + str(self.getLeader()))
        
            
    def __init__(self, servername=socket.gethostbyname(socket.gethostname()), 
                 port=5555,
                 onMessageReceived=None,
                 onPlayerAdded=None,
                 onPlayerRemoved=None):
        self._matchmaker = matchmaker.matchmaker(servername=servername, port=port, handler=self._handleMsg)
        self._timers = {}
        self._matchmaker.onPlayerAdded = self._addPlayer
        self._matchmaker.onPlayerRemoved = self._removePlayer
        self._logFile = open(self._getLog(), 'w')
        self._lostPlayers = {}
        t = threading.Timer(5,self._heartbeat)
        t.daemon = True
        t.start()
        self._msgHandler = onMessageReceived
        self._playerAddedHander = onPlayerAdded
        self._playerRemovedHander = onPlayerRemoved
        
    def _heartbeat(self):
        for player in self.getPlayers():
            self.send(player, 'ping')
        t = threading.Timer(5,self._heartbeat)
        t.daemon = True
        t.start()
        
    def log(self, msg):
        self._logFile.write('[' + time.asctime() + '] ' + msg + '\n')
        self._logFile.flush()    
    def _getLog(self):
        file_lock.acquire()
        files = os.listdir('logs')
        curFile = 0
        for file in files:
            m = re.match(str(os.getpid()) + '_(\d)\.log', file)
            if m != None:
                i = int(m.group(1))
                if i >= curFile:
                    curFile = i + 1
        file = 'logs/' + str(os.getpid()) + '_' + str(curFile) + '.log'
        f = open(file, 'w')
        f.close()
        file_lock.release()
        return file

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
