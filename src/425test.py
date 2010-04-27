import sys

bops = {'FLOOR':2, 'WALL':1, 'DOT':0, 'SUPER_DOT':3}
board = []
inFile = open('board.txt', 'r', 1)
for line in inFile:
    temp = []
    for char in line[0:30]:
        temp.append(int(char))
    board.append(temp)
inFile.close()
