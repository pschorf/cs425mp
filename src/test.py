import game, time, threading

NUM_CLIENTS = 20

def runClient():
    foo = game.game()

for i in range(NUM_CLIENTS):
    t = threading.Thread(target=runClient)
    t.daemon = True
    t.start()
time.sleep(30)
    

