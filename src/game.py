import board, client, sys, threading, Queue
     
dirs = {'LEFT':0, 'RIGHT':1, 'UP':2, 'DOWN':3}
sops = {'PACMAN':0, 'GHOST':1}
board = board.board()
mlock = threading.RLock()

class state(object):
    global dirs, board, sops
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
                self._y = self._y + 1
                self._dir = dir
            elif (dir == dirs['DOWN']):
                self._y = self._y - 1
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
    def disc(self):
        self._c.disconnect()
    def printStates2(self):
        print str(self._states)
    def printStates(self):
        for k in self._states:
            self._states[k].printPos()
    def __init__(self):
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
        self._c = client.client(name, port, self._handleMsg, self._playerAdded, self._playerRemoved)
        players = self._c.findGame()
        if not players:
            self._states[self._c.getSelf()] = state(sops['PACMAN'])
        else:
            self._numPlayers = len(players) + 1
            if self._numPlayers == 5:
                self._play = True
            for p in players:
                if self._c.getLeader() == p:
                    self._states[p] = state(sops['PACMAN']) 
                else:
                    self._states[p] = state(sops['GHOST'])
            self._states[self._c.getSelf()] = state(sops['GHOST'])
        print str(self._numPlayers)
        intervalExecute(1.0, self.update)
        inputThread = threading.Thread(target=self._input)
        inputThread.daemon = True
        inputThread.start()
    def _playerAdded(self, player):
        self._states[player] = state(sops['GHOST'])
        self._numPlayers += 1
        if self._numPlayers == 5:
            self._play = True
    def _playerRemoved(self, player):
        self._numPlayers -= 1
        self._play = False
        del self._states[player]
    def _handleMsg(self, msg, source):
        self._c.log('received ' + msg + ' from ' + str(source))
        if self._play:
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
        while not self._msgs.empty():
            mlock.acquire()
            q = self._msgs.get()
            mlock.release()
            self._c.sendToAll(q)
    def _input(self):
        f = open('input', 'r')
        for m in f:
            while not self._play:
                continue
            mlock.acquire()
            if m[0:1] == 'L':
                self._msgs.put('LEFT')
                self._states[self._c.getSelf()].move(dirs['LEFT'])
            elif m[0:1] == 'R':
                print 'RIGHT'
                self._msgs.put('RIGHT')
                self._states[self._c.getSelf()].move(dirs['RIGHT'])
            elif m[0:1] == 'U':
                self._msgs.put('UP')
                self._states[self._c.getSelf()].move(dirs['UP'])
            elif m[0:1] == 'D':
                self._msgs.put('DOWN')
                self._states[self._c.getSelf()].move(dirs['DOWN'])
            mlock.release()
        f.close()