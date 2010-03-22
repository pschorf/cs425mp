
bops = {'FLOOR':0, 'WALL':1, 'DOT':2, 'SUPER_DOT':3}
dirs = {'LEFT':0, 'RIGHT':1, 'UP':2, 'DOWN':3}
class board(object):
    global bops, dirs
    def __init__(self):
        self._board = []
        inFile = open('board', 'r', 1)
        for line in inFile:
            temp = []
            for char in line[0:30]:
                temp.append(int(char))
            self._board.append(temp)
        inFile.close()
    def canMove(self, dir, (x, y)):
        '''try:
            switch(dir):
			case dirs['LEFT']:
				if(self._board[x-1][y] not 1):
					return True
				break
			case dirs['RIGHT']:
				if(self._board[x+1][y] not 1):
					return True
				break
			case dirs['UP']:
				if(self._board[x][y-1] not 1):
					return True
				break
			case dirs['DOWN']:
				if(self._board[x][y+1] not 1):
					return True
				break
			}
			return False
		except:
			return False'''
        return True
    def pacmanStart(self):
        return (0, 0, dirs['LEFT'])
        #return (2, 1, dirs['LEFT'])
    def ghostStart(self):
        return (0, 0, dirs['LEFT'])
        #return (2, 24, dirs['UP'])