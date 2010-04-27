## @package board
# Defines the board
# @author Myles Megyesi

## @var bops 
# Defines options for tiles on the board
bops = {'FLOOR':0, 'WALL':1, 'DOT':2, 'SUPER_DOT':3}    
## @var dirs
# Defines the directions for movement
dirs = {'LEFT':0, 'RIGHT':1, 'UP':2, 'DOWN':3}

## A class to define the board
class board(object):
    global bops, dirs
    ## Constructor
    def __init__(self):
        self.board = []
        inFile = open('board', 'r')
        for line in inFile:
            temp = []
            for char in line[0:30]:
                temp.append(int(char))
            self.board.append(temp)
        inFile.close()
    ## Given a direction and your current position, returns whether you a making a valid move
    # @param dir The direction to move
    # @param (x, y) A tuple of your x and y coordinates
    # @return A boolean indicating a valid move
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
    ## Defines the starting position for a PACMAN player
    # @return a tuple coordinates and position of the PACMAN start 
    def pacmanStart(self):
        return (2, 1, dirs['LEFT'])
    ## Defines the starting position for a Ghost player
    # @return A tuple coordinates and position of the Ghost start 
    def ghostStart(self):
        return (2, 24, dirs['UP'])
    
## @cond USELESS
if __name__ == "__main__":
    
## @endcond