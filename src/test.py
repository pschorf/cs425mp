import game, time, threading

NUM_CLIENTS = 500

for i in range(NUM_CLIENTS):
    t = threading.Thread(target=runClient)
    
def runClient():
    foo = game.game()
    time.sleep(30)
