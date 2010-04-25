'''
Created on Feb 22, 2010

@author: Paul
'''

import re, threading, socket, weakref, time, sqlite3

class matchmaker(object):
    '''
    A class to help control the interface with the matchmaking server
    '''
    
    def getLeader(self):
        return self._leader
    
    def getAddress(self):
        return self._addr
    
    def changeLeader(self):
        
        newLeader = self._otherPlayers[0]
        oldLeader = self._leader
        self._leader = newLeader
        self._otherPlayers.remove(newLeader)
        if self._leader == self._addr:
            self.send((self._nameserver, self._nsport), 'LEADER-CHANGE##' + str(oldLeader) + '##' + str(newLeader))
            self._pingThread = threading.Timer(15,self._ping)
            self._pingThread.daemon = True
            self._pingThread.start()
        if self._onLeaderChange != None:
            self._onLeaderChange(newLeader)
    
    def getPlayers(self): 
        return [p for p in self._otherPlayers + [self._leader] if p != self._addr and p != None]
    
    def removePlayer(self, player):
        self._removePlayer(player)
        if self.getLeader() == self.getAddress():
            self._requestNewPlayer()
        
    def findGame(self):
        if self._leader == None:
            self._getGame()
        return self.getPlayers()
    
    def disconnect(self):
        if self._addr == self._leader:
            for player in self.getPlayers():
                self.send(player, 'LEADER-ELECT##' + str(self._addr))
        for player in self.getPlayers():
            self.send(player, 'DISCONNECT##' + str(self._addr))
        self._otherPlayers = []
        self._leader = None
        if self._pingThread != None:
            self._pingThread.cancel()
        
    def _requestNewPlayer(self):
        if self._addr != self._leader:
            return
        else:
            self.send((self._nameserver,self._nsport), 'ADDPLAYER')
        
    def _getGame(self,attempt=4):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(45)
        try:
            sock.connect((self._nameserver, self._nsport))
    	except:
	    sock.close()
	    if attempt > 0:
                time.sleep(10)
                self._getGame(attempt-1)
                return
            else:
                raise
        self._addr = sock.getsockname()
        sock.send(str(self._addr) + '###JOIN')
        resp = sock.recv(1024)
        if resp.find('NEWGAME') > -1:
            self._leader = self._addr
            sock.close()
            t = threading.Thread(target=self._listen,args=[self._addr])
            t.daemon = True
            t.start()
            t = threading.Timer(15,self._ping)
            t.daemon = True
            t.start()
            return
        else:
            m = re.match('JOIN \(\'([\d\.]+)\', (\d+)\)', resp)
            self._joinGame((m.group(1), int(m.group(2))),attempt)
                     
    def _joinGame(self, game_addr,attempt=3):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(game_addr)
        except:
            if attempt > 0:
                time.sleep(10)
                return self._getGame(attempt-1)
            else:
                raise
        self._addr = sock.getsockname()
        sock.send(str(self._addr) + '###JOIN')
        try:
            resp = sock.recv(1024)
        except:
            self._getGame()
            return
        if resp.find('SUCCESS') > -1:
            arr = resp.split('##')
            arr = arr[1:len(arr)]
            for s in arr:
                m = re.match('\(\'([\d\.]+)\', (\d+)\)', s)
                if m != None:
                    self._addPlayer((m.group(1), int(m.group(2))))
            self._addPlayer(self._addr)
            self._leader = game_addr
            sock.close()
            t = threading.Thread(target=self._listen,args=[self._addr])
            t.daemon = True
            t.start()
    
    def _handleRequest(self, client, client_addr):
        resp = client.recv(1024)
        source_addr = ()
        arr = resp.split('###')
        if len(arr) < 2:
            print str(arr)
            return
        else:
            resp = arr[1]
            source_addr = parseAddr(arr[0])
        if resp.find('JOIN') == 0 and self._leader == self._addr:
            client.send('SUCCESS' + formatPlayers(self._otherPlayers))
            for player in self._otherPlayers:
                self.send(player, 'NEWPLAYER' + str(source_addr))
            self._addPlayer(client_addr)
        elif resp.find('NEWPLAYER') == 0:
            self._addPlayer(parseAddr(resp))
        elif resp.find('DISCONNECT') == 0:
            self.removePlayer(source_addr)
        else:
            self._handler(resp, source_addr)
            
    def send(self, addr, message):
        if self._leader == None:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(addr)
            sock.send(str(self._addr) + '###' + message)
        except:
            pass
    
    def _addPlayer(self, player):
        self._otherPlayers.append(player)
        if self.onPlayerAdded != None and player != self._addr:
            self.onPlayerAdded(player)
    
    def _removePlayer(self, player):
        if player in self._otherPlayers:
            self._otherPlayers.remove(player)
        if self.onPlayerRemoved != None and player != self._addr:
            self.onPlayerRemoved(player)
    
    def _listen(self, addr):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(addr)
        sock.listen(50)
        while 1:
            try:
                (client, client_addr) = sock.accept()
                self._handleRequest(client, client_addr)
            except:
                pass
    def _ping(self):
        self.send((self._nameserver, self._nsport), 'PING')
        if self._leader == self._addr:
            self._pingThread = threading.Timer(15, self._ping)
            self._pingThread.daemon = True
            self._pingThread.start()

    def __init__(self, servername=socket.gethostbyname(socket.gethostname()), 
                 port=5555,handler=None,
                 onLeaderChanged=None):
        self._nameserver = servername
        self._nsport = port
        self._otherPlayers = []
        self._leader = None
        self._addr = None
        self._pingThread = None
        self._handler = handler
        self._onLeaderChange = onLeaderChanged
        if self._handler == None:
            self._handler = lambda k, y: k

def _dummy(text, source):
    pass  
        

def formatPlayers(players):
    s = '##'
    for player in players:
        s += str(player) + '##'
    s = s[0:len(s)-2]
    return s
        
def parseAddr(s):
    m = re.search('\(\'([\d\.]+)\', (\d+)\)', s)
    try:
        return (m.group(1), int(m.group(2)))
    except:
        pass
        
