import board, client, sys, threading, Queue, pickle, time
     
dirs = {'LEFT':0, 'RIGHT':1, 'UP':2, 'DOWN':3}
sops = {'PACMAN':0, 'GHOST':1}
board = board.board()
mlock = threading.RLock()

class state(object):
    global dirs, board, sops
    def getState(self):
        return (self._x, self._y, self._dir, self._type)
    def setState(self, x, y, dir, type):
        self._x = x
        self._y = y
        self._dir = dir
        self._type = type
    def printPos(self):
        print '(x: ' + str(self._x) + ', y: ' + str(self._y) + ', Type: ' + str(self._type) + ')'
    def move(self, dir):
        if board.canMove(dir, (self._x, self._y)):
            if (dir == dirs['LEFT']):
                self._x = self._x - 1
                self._dir = dir
            elif (dir == dirs['RIGHT']):
                self._x = self._x + 1
                self._dir = dir
            elif (dir == dirs['UP']):
                self._y = self._y - 1
                self._dir = dir
            elif (dir == dirs['DOWN']):
                self._y = self._y + 1
                self._dir = dir
    def __init__(self, type):
        if type == sops['PACMAN']:
            (self._x, self._y, self._dir) = board.pacmanStart()
        elif type == sops['GHOST']:
            (self._x, self._y, self._dir) = board.ghostStart()
        self._type = type
            
def intervalExecute(interval, func, *args, **argd):
    ''' @param interval: execute func(*args, **argd) each interval
        @return: a callable object to enable you terminate the timer.
    '''
    cancelled = threading.Event()
    def threadProc(*args, **argd):
        while True:
            cancelled.wait(interval)
            if cancelled.isSet():
                break
            func(*args, **argd) #: could be a lenthy operation
    th = threading.Thread(target=threadProc, args=args, kwargs=argd)
    th.daemon = True
    th.start()
    

class game(object):
    global msgs, dirs, sops
    def disconnect(self):
        self._c.disconnect()
    def printStates2(self):
        print str(self._states)
    def printStates(self):
        print str(self._c.getSelf())
        for k in self._states:
            self._states[k].printPos()
    def __init__(self):
        self._holding = Queue.Queue()
        self._msgs = Queue.Queue()
        self._play = False
        self._numPlayers = 1
        self._states = {}
        name = '192.168.1.129'
        port = 5555
        if len(sys.argv) >= 2:
            name = sys.argv[1]
        if len(sys.argv) >= 3:
            port = int(sys.argv[2])
        self._c = client.client(name, port, self._handleMsg, self._playerAdded, self._playerRemoved, self._newLeader)
        players = self._c.findGame()
        if not players:
            self._states[self._c.getSelf()] = state(sops['PACMAN'])
        intervalExecute(1.0, self.update)
        inputThread = threading.Thread(target=self._input)
        inputThread.daemon = True
        inputThread.start()
    def _newLeader(self, player):
        if player == self._c.getSelf():
            
    def _playerAdded(self, player):
        if player == None:
            return
        self._states[player] = state(sops['GHOST'])
        if self._c.getLeader() == self._c.getSelf():
            time.sleep(0.25)
            self._sync(player)
        self._numPlayers += 1
        if self._numPlayers == 5:
            self._c.log('STARTING GAME')
            self._play = True
    def _playerRemoved(self, player):
        self._numPlayers -= 1
        self._c.log('STOPPING GAME')
        self._play = False
        del self._states[player]
    def _handleMsg(self, msg, source):
        if msg.find('SYNCNEWPLAYER') > -1:
            s = msg.split('SYNCNEWPLAYER ')[1]
            pstr = pickle.loads(s)
            for k in pstr:
                (x, y, dir, type) = pickle.loads(pstr[k])
                self._states[k] = state(type)
                self._states[k].setState(x, y, dir, type)
            self._numPlayers = len(pstr)
            if self._numPlayers == 5:
                self._c.log('STARTING GAME')
                self._play = True
        elif not self._play:
            self._holding.put((msg, source))
        else:
            if msg[0:4] == 'LEFT':
                self._states[source].move(dirs['LEFT'])
            elif msg[0:5] == 'RIGHT':
                self._states[source].move(dirs['RIGHT'])
            elif msg[0:2] == 'UP':
                self._states[source].move(dirs['UP'])
            elif msg[0:4] == 'DOWN':
                self._states[source].move(dirs['DOWN'])
    def update(self):
        if not self._play:
            return
        while not self._holding.empty():
            (msg, source) = self._holding.get()
            self._handleMsg(msg, source)
        while not self._msgs.empty():
            mlock.acquire()
            q = self._msgs.get()
            if q == 'LEFT':
                self._states[self._c.getSelf()].move(dirs['LEFT'])
            elif q == 'RIGHT':
                self._states[self._c.getSelf()].move(dirs['RIGHT'])
            elif q == 'UP':
                self._states[self._c.getSelf()].move(dirs['UP'])
            elif q == 'DOWN':
                self._states[self._c.getSelf()].move(dirs['DOWN'])
            mlock.release()
            self._c.sendToAll(q)
    def _input(self):
        f = open('input', 'r')
        for m in f:
            mlock.acquire()
            if m[0:1] == 'L':
                self._msgs.put('LEFT')
            elif m[0:1] == 'R':
                print 'RIGHT'
                self._msgs.put('RIGHT')
            elif m[0:1] == 'U':
                self._msgs.put('UP')
            elif m[0:1] == 'D':
                self._msgs.put('DOWN')
            mlock.release()
        f.close()
    def _sync(self, player):
        senddict = {}
        for p in self._states:
            senddict[p] = pickle.dumps(self._states[p].getState())
        pstr = 'SYNCNEWPLAYER ' + pickle.dumps(senddict)
        self._c.send(player, pstr)