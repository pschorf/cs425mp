import game, threading

NUM_CLIENTS = 100

def runClient():
    foo = game.game(60)
for i in range(NUM_CLIENTS):
    t = threading.Thread(target=runClient)
    t.daemon = False
    t.start()