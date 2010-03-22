import board, client, socket, sys, threading, Queue

class Enumerate(object):
    def _init_(self, names):
        for number, name in enumerate(names.split()):
            setattr(self, name, number)
            
dirs = Enumerate('LEFT RIGHT UP DOWN')
board = board()
msgs = Queue()
mlock = threading.Lock()

class state(object):
    global dirs, board, msgs
    def move(self, dir):
        if board.canMove(dir):
            if (dir == dirs.LEFT):
                self._x = self._x - 1
                self._dir = dir
            if (dir == dirs.RIGHT):
                self._x = self._x + 1
                self._dir = dir
            if (dir == dirs.UP):
                self._x = self._y + 1
                self._dir = dir
            if (dir == dirs.DOWN):
                self._x = self._y - 1
                self._dir = dir
    def __init__(self):
        self._dir = dirs.LEFT
        self._x = 0
        self._y = 0

class game(object):
    global msgs, dirs
    def __init__(self):
        self._play
        self._numPlayers = 1
        self._states = {}
        name = socket.gethostbyname(socket.gethostname())
        port = 5555
        if len(sys.argv) >= 2:
            name = sys.argv[1]
        if len(sys.argv) >= 3:
            port = int(sys.argv[2])
        self._c = client(name, port)
        self._c.findGame()
        updateThread = threading.Timer(1, self._update)
        updateThread.daemon = True
        updateThread.start()
        inputThread = threading.Thread(self._input)
        inputThread.daemon = True
        inputThread.start()
    def playerAdded(self, player):
        self._states[player] = state()
        self._numPlayers += 1
        if self._numPlayers == 5:
            self._play = True
    def playerRemoved(self, player):
        self._numPlayers -= 1
        self._play = False
        del self._states[player]
    def _handleMsg(self, msg, source):
        self._log('received ' + msg + ' from ' + str(source))
        if self._play:
            if msg.find('LEFT') > -1:
                self._states[source].move(dirs.LEFT)
            if msg.find('RIGHT') > -1:
                self._states[source].move(dirs.RIGHT)
            if msg.find('UP') > -1:
                self._states[source].move(dirs.UP)
            if msg.find('DOWN') > -1:
                self._states[source].move(dirs.DOWN)
    def _update(self):
        if not self._play:
            return
        while not msgs.Empty():
            mlock.aquire()
            q = msgs.get()
            mlock.release()
            self._c.sendall(q) 
    def _input(self):
        while not self._play:
            continue
        f = open('input.txt', 'r')
        while f:
            m = f.read(1)
            mlock.aquire()
            if m.find('L'):
                msgs.put('LEFT')
            if m.find('R'):
                msgs.put('RIGHT')
            if m.find('U'):
                msgs.put('UP')
            if m.find('D'):
                msgs.put('DOWN')
            mlock.release()
        f.close()
                