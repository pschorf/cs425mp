for /l %%X in (1, 1, 5) do (start python test.py 192.168.1.124)                 
for /l %%X in (1, 1, 1) do (start python game.py 192.168.1.124 --quiet --unsafe)                 
