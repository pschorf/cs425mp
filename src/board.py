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
        ## @var board
        # An array representing the board
        self.board = []
        ## @var totalScore
        # The total game score
        self.totalScore = 0
        ## @var pacScore
        # PacMan's score
        self.pacScore = 0
        inFile = open('board', 'r')
        for line in inFile:
            temp = []
            for char in line[0:30]:
                temp.append(int(char))
                if(int(char) == 2):
                    self.totalScore += 1
                elif(int(char) == 3):
                    self.totalScore += 3
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
    ## Removes a dot from the board, updates score
	# @param (x, y) A tuple of x and y coords
    def eatDot(self, (x, y)):
        if(self.board[y][x] == bops['DOT']):
            self.pacScore += 1
        elif(self.board[y][x] == bops['SUPER_DOT']):
            selfpacScore += 3
        self.board[y][x] = bops['FLOOR']
    ## Defines the starting position for a PACMAN player
    # @return a tuple coordinates and position of the PACMAN start 
    def pacmanStart(self):
        return (2, 1, dirs['LEFT'])
    ## Defines the starting position for a Ghost player
    # @return A tuple coordinates and position of the Ghost start 
    def ghostStart(self):
        return (2, 24, dirs['UP'])
    ## Returns pac's score
    #
    def pacScores(self):
        return self.pacScore
    ## Returns ghost's score
    #
    def ghostScores(self):
        return (self.totalScore - self.pacScore)
    
## @cond USELESS
#if __name__ == "__main__":
    
## @endcond
