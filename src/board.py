
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
            board.append(temp)
        inFile.close()
    def canMove(self, dir, (x, y)):
        return True
    def pacmanStart(self):
        return (0, 0, dirs['LEFT'])
    def ghostStart(self):
        return (0, 0, dirs['UP'])