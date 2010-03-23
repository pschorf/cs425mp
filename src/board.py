
bops = {'FLOOR':0, 'WALL':1, 'DOT':2, 'SUPER_DOT':3}
dirs = {'LEFT':0, 'RIGHT':1, 'UP':2, 'DOWN':3}
class board(object):
    global bops, dirs
    def __init__(self):
        self.board = []
        inFile = open('board', 'r')
        for line in inFile:
            temp = []
            for char in line[0:30]:
                temp.append(int(char))
            self.board.append(temp)
        inFile.close()
    def canMove(self, dir, (x, y)):
        try:
            if(dir == dirs['LEFT']):
                if(self.board[y][x-1] != bops['WALL']):
                    return True
            elif(dir == dirs['RIGHT']):
                if(self.board[y][x+1] != bops['WALL']):
                    return True
            elif(dir == dirs['UP']):
                if(self.board[y-1][x] != bops['WALL']):
                    return True
            elif(dir == dirs['DOWN']):
                if(self.board[y+1][x] != bops['WALL']):
                    return True
            return False
        except:
            return False
        return True
    def pacmanStart(self):
        return (2, 1, dirs['LEFT'])
    def ghostStart(self):
        return (2, 24, dirs['UP'])