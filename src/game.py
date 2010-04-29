## @package game 
# Controls the game state and handles the operation of the game
# @author Myles Megyesi

import board, client, sys, threading, Queue, pickle, time, os, random, getopt, Console, msvcrt

## @var dirs 
# Defines the directions for movement
dirs = {'LEFT':0, 'RIGHT':1, 'UP':2, 'DOWN':3}
## @var sops 
#Defines the player types
sops = {'PACMAN':0, 'GHOST':1}
## @var board 
# The global playing board
board = board.board()
## @var mlock 
# A semaphore used to when pushing or popping the messages queue
mlock = threading.RLock()
## @var update_interval 
#The interval at which to run the the game loop
update_interval = .1

## @var pacx
#store pac's position
pacx = 0
## @var pacy
#store pac's position
pacy = 0


#######

##get input from keyboard
def kbpass():
    if msvcrt.kbhit():
        return ord(msvcrt.getch())
    else:
        return 0

## Defines the player's state
class state(object):
    global dirs, board, sops
    
    ## Changes the type of player. Used during leader election
    # @param type The player type to change to
    def changeType(self, type):
        self._type = type
    ## State getter
    # @return The state of the player
    def getState(self):
        return (self._x, self._y, self._dir, self._type)
    ## State setter
    # @param x The X coordinate
    # @param y The Y coordinate
    # @param dir the direction to face
    # @param type The type of the player
    def setState(self, x, y, dir, type):
        self._x = x
        self._y = y
        self._dir = dir
        self._type = type
    ## Move the player one space in a given direction
    # @param dir The direction to move the player
    def move(self, dir):
        if board.canMove(dir, (self._x, self._y)):
            if (dir == dirs['LEFT']):
                self._x -= 1
                self._dir = dir
            elif (dir == dirs['RIGHT']):
                self._x += 1
                self._dir = dir
            elif (dir == dirs['UP']):
                self._y -= 1
                self._dir = dir
            elif (dir == dirs['DOWN']):
                self._y += 1
                self._dir = dir
            if(self._type == sops['PACMAN']):
                board.eatDot((self._x, self._y))
    ## Constructor
    # @param type The type to make the player
    def __init__(self, type):
        if type == sops['PACMAN']:
            (self._x, self._y, self._dir) = board.pacmanStart()
        elif type == sops['GHOST']:
            (self._x, self._y, self._dir) = board.ghostStart()
        self._type = type

## Executes a function repeatedly at the given interval
# @param interval executes func(*args, **argd) each interval
# @return a callable object to enable you terminate the timer
def intervalExecute(interval, func, *args, **argd):
    cancelled = threading.Event()
    def threadProc(*args, **argd):
        while True:
            cancelled.wait(interval)
            if cancelled.isSet():
                break
            func(*args, **argd)
    th = threading.Thread(target=threadProc, args=args, kwargs=argd)
    th.daemon = True
    th.start()
    
## A class to control the game
class game(object):
    global msgs, dirs, sops, board, update_interval
	
	#input keys
    global keyLeft, keyRight, keyUp, keyDown
	
    ## Disconnects the player from the socket, used upon exit of game
    def disconnect(self):
        self._c.disconnect
    ## @cond TESTING_PRINT
    def printStates2(self):
        print str(self._states)
    def printStates(self):
        print str(self._c.getSelf())
        for k in self._states:
            print self._states[k].getState()
    ## @endcond
    
    ## Draws the board on the screen, with the players
    def draw(self):
        global pacx, pacy
        tempit = 0
        temp = []
        for arr in board.board:
            temp.append([])
            for char in arr:
                temp[tempit].append(char)
            tempit += 1
        for k in self._states:
            (x, y, dir, type) = self._states[k].getState()
            if type == sops['PACMAN']:
                temp[y][x] = '\01'
                pacx = x
                pacy = y
            elif type == sops['GHOST']:
                temp[y][x] = '\04'
                if (x == pacx):
                    if(y == pacy):
                        self.gameOver = True
		iter = 0
        for arr in temp:
            baz = ''
            for num in arr:
                baz += str(num)
            self.gameCon.text(0, iter, baz)
            iter += 1
        if(self._states[self._c.getSelf()]._type == sops['PACMAN']):
            self.gameCon.text(40, 0, "EAT THE PELLETS", 0x3f)
            self.gameCon.text(40, 1, "SCORE", 0x2f)
            self.gameCon.text(40, 2, str(board.pacScores()), 0x1f)
        elif(self._states[self._c.getSelf()]._type == sops['GHOST']):
            self.gameCon.text(40, 0, "KILL THE DUDE", 0x3f)
            self.gameCon.text(40, 1, "SCORE", 0x2f)
            self.gameCon.text(40, 2, str(board.ghostScores()), 0x1f)
        if(self.gameOver):
            self.gameCon.text(40,5, "GAME OVER")
    ## Constructor
    # @param server_ip The IP address of the server
    # @param server_port The port of the server
    # @param wait_time The time to run the game. If not set, the game will run indefinitely
    # @param isSafe Boolean to toggle the timeout threads on and off
    # @param printStates Boolean to toggle the drawing on and off
    # @param aiType Boolean to toggle the AI
    def __init__(self, server_ip, 
                 server_port=5555,
                 wait_time=None,
                 isSafe=True,
                 printStates=True,
                aiType=False):
        ## @cond KEYBOARD_CONSTANTS
	self.keyLeft = 75
	self.keyRight = 77
	self.keyUp = 72
	self.keyDown = 80
        ## @endcond
        ## @var self.isAI
        # False if human-controlled
        self.isAI = aiType
        ## @var self._holding
        # A queue for messages recieve while the game is not yet in play
        self._holding = Queue.Queue()
        ## @var self._msgs
        # A queue for the messages recieved
        self._msgs = Queue.Queue()
        ## @var self._play
        # A boolean to trigger the game play. Game loop won't run until true
        self._play = False
        ## @var self._numPlayers
        # The number of players currently in the game
        self._numPlayers = 1
        ## @var self._states
        # A dictionary of all the players states
        self._states = {}
        ## @var self._shouldPrint
        # A toggle for the state printing
        self._shouldPrint = printStates
        ## @var self._c
        # A Client object
        self._c = client.client(server_ip, server_port, self._handleMsg, self._playerAdded, self._playerRemoved, self._newLeader,isSafe)
        players = self._c.findGame()
        ## @var self.gameOver
        #game is over
        self.gameOver = False
        ## @var self.gameCon
        #better control of the screen
        self.gameCon = Console.getconsole()
        if not players:
            self._states[self._c.getSelf()] = state(sops['PACMAN'])
        inputThread = threading.Thread(target=self._input)
        inputThread.daemon = True
        inputThread.start()
        self._run(server_ip, server_port, wait_time, isSafe, printStates)
    ## runs the game, starts a new one if desired
    # @param server_ip The IP address of the server
    # @param server_port The port of the server
    # @param wait_time The time to run the game. If not set, the game will run indefinitely
    # @param isSafe Boolean to toggle the timeout threads on and off
    # @param printStates Boolean to toggle the drawing on and off
    def _run(self, server_ip, 
	            server_port,
                wait_time,
                isSafe,
                printStates):
        if wait_time==None:
            while self.gameOver == False:
                time.sleep(update_interval)
                self.update()
        else:
            intervalExecute(update_interval, self.update)
            time.sleep(wait_time)
        self.gameCon.page()
        self.gameCon.text(0,0, "play again?")
        self.gameOver = self.isAI
        while self.gameOver == False:
            foo = kbpass()
            if foo == self.keyLeft:
                self.gameOver = true
            elif foo == self.keyRight:
		self.gameCon.text(5,5,"FINDING GAME")
                ## @var self._holding
                # A queue for messages recieve while the game is not yet in play
                self._holding = Queue.Queue()
                ## @var self._msgs
                # A queue for the messages recieved
                self._msgs = Queue.Queue()
                ## @var self._play
                # A boolean to trigger the game play. Game loop won't run until true
                self._play = False
                ## @var self._numPlayers
                # The number of players currently in the game
                self._numPlayers = 1
                ## @var self._states
                # A dictionary of all the players states
                self._states = {}
                ## @var self._shouldPrint
                # A toggle for the state printing
                self._shouldPrint = printStates
                ## @var self._c
                # A Client object
                self._c = client.client(server_ip, server_port, self._handleMsg, self._playerAdded, self._playerRemoved, self._newLeader,isSafe)
                players = self._c.findGame()
                ## @var self.gameOver
                #game is over
                self.gameOver = False
                ## @var self.gameCon
                #better control of the screen
                if not players:
                    self._states[self._c.getSelf()] = state(sops['PACMAN'])
                self._run(server_ip, server_port, wait_time, isSafe, printStates)
		self.gameOver = True
    ## Changes the leader of the game
    # @param player The new leader
    def _newLeader(self, player):
        if player == self._c.getSelf():
            self._states[player].changeType(sops['PACMAN'])
    ## Adds a player to the game
    # @param The player to be added
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
    ## Removes a player from the game
    # @param player The player to be removed
    def _playerRemoved(self, player):
        self._numPlayers -= 1
        if self._numPlayers == 4:
            self._c.log('STOPPING GAME')
        self._play = False
        del self._states[player]
    ## Handles incoming messages from other players (syncs, moves, etc.)
    # @param msg The messages to handle
    # @param source The player that sent the message
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
    ## The game loop
    def update(self):
        if self.gameOver:
            return
        if not self._play:
            return
        while not self._holding.empty():
            (msg, source) = self._holding.get()
            self._handleMsg(msg, source)
        #keyboard input
	if self.isAI == False:
		myDir = kbpass()
	elif self.isAI == True:
		myDir = random.randint(0, 3)
		if myDir == 0:
			myDir = self.keyLeft
		elif myDir == 1:
			myDir = self.keyRight
		elif myDir == 2:
			myDir = self.keyUp
		elif myDir == 3:
			myDir = self.keyDown
	if myDir == self.keyLeft:
	    self._msgs.put(0)
	elif myDir == self.keyRight:
	    self._msgs.put(1)
	elif myDir == self.keyUp:
	    self._msgs.put(2)
	elif myDir == self.keyDown:
	    self._msgs.put(3)
        while not self._msgs.empty():
            mlock.acquire()
            q = self._msgs.get()
            if not self._c.getSelf() in self._states:
                mlock.release()
                continue
            if q == dirs['LEFT']:
                self._c.sendToAll('LEFT')
                self._states[self._c.getSelf()].move(dirs['LEFT'])
            elif q == dirs['RIGHT']:
                self._c.sendToAll('RIGHT')
                self._states[self._c.getSelf()].move(dirs['RIGHT'])
            elif q == dirs['UP']:
                self._c.sendToAll('UP')
                self._states[self._c.getSelf()].move(dirs['UP'])
            elif q == dirs['DOWN']:
                self._c.sendToAll('DOWN')
                self._states[self._c.getSelf()].move(dirs['DOWN'])
            mlock.release()
        if self._shouldPrint:
            self.draw()
    ## Accepts file input
    def _input(self):
        f = open('input', 'r')
        for m in f:
            mlock.acquire()
            if m[0:1] == 'L':
                self._msgs.put(dirs['LEFT'])
            elif m[0:1] == 'R':
                self._msgs.put(dirs['RIGHT'])
            elif m[0:1] == 'U':
                self._msgs.put(dirs['UP'])
            elif m[0:1] == 'D':
                self._msgs.put(dirs['DOWN'])
            mlock.release()
        f.close()
    ## Syncronizes the current game state of all players with a given player
    # @param The player to syncronize with
    def _sync(self, player):
        senddict = {}
        for p in self._states:
            senddict[p] = pickle.dumps(self._states[p].getState())
        pstr = 'SYNCNEWPLAYER ' + pickle.dumps(senddict)
        self._c.send(player, pstr)
      
## @cond RUN_FROM_COMMAND_LINE
if __name__ == "__main__":
    port =5555
    safe = True
    doPrint = True
    ai = False
    args = []
    if len(sys.argv) < 2:
        print 'Usage: ' + sys.argv[0] + ' server_ip -p <server_port> -a -u -q'
        exit(0)
    elif len(sys.argv) >= 2:
        ip = sys.argv[1]
        args = sys.argv[2:]
    if not args == []:
        opts, args = getopt.getopt(args, "uqpa:", ["unsafe", "quiet", "port=", "ai"])
        for opt, arg in opts:
            if opt in ("u", "--unsafe"):
                safe = False
            elif opt in ("q", "--quiet"):
                doPrint = False
            elif opt in ("p","--port="):
                port = int(arg)
            elif opt in ("a", "--ai"):
                ai = True
	print doPrint
    f = game(ip, port, None,isSafe=safe,printStates=doPrint, aiType = ai)
## @endcond