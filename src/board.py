class Enumerate(object):
    def _init_(self, names):
        for number, name in enumerate(names.split()):
            setattr(self, name, number)
bops = Enumerate('FLOOR WALL DOT SUPER_DOT')

class board(object):
    global bops
    def __init__(self):
        b = []
        #first two rows are wall
        b.append([])
        for i in xrange(30):
            b[0][i] = bops.WALL
        for i in xrange(30):
            b[1][i] = bops.WALL
        #third row
        b.append([])
        b[2][0] = bops.WALL
        b[2][1] = bops.WALL
        for i in xrange(12):
            b[1][i+2] = bops.DOT
        b[2][14] = bops.WALL
        b[2][15] = bops.WALL
        for i in xrange(12):
            b[2][i+15] = bops.DOT
        b[2][28] = bops.WALL
        b[2][29] = bops.WALL
        #fourth row
        b.append([])
        b[3][0] = bops.WALL
        b[3][1] = bops.WALL
        b[3][2] = bops.DOT
        for i in xrange(4):
            b[3][i+3] = bops.WALL
        b[3][7] = bops.DOT
        for i in xrange(5):
            b[3][i+7] = bops.WALL
        b[3][13] = bops.DOT
        b[3][14] = bops.WALL
        b[3][15] = bops.WALL
        b[3][16] = bops.DOT
        for i in xrange(5):
            b[3][i+16] = bops.WALL
        b[3][22] = bops.DOT
        for i in xrange(4):
            b[3][i+22] = bops.WALL
        b[3][27] = bops.DOT
        b[3][28] = bops.WALL
        b[3][29] = bops.WALL
        #fifth row
    def canMove(self, dir):
        return True