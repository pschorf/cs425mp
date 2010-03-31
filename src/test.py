import game, threading

NUM_CLIENTS = 166
threads = []
count = 1
def runClient():
    foo = game.game(60)
for i in range(NUM_CLIENTS):
    t = threading.Thread(target=runClient)
    t.daemon = False
    t.start()
    threads.append(t)
for t in threads:
    t.join()
    print str(count) + ' threads joined'
    count = count + 1

raw_input()
