from datetime import datetime
from numpy.random import default_rng
rng = default_rng()

import util

run_time = datetime.now().strftime("%Y%m%d%H%M%S")
folder_path = f"/results/{run_time}"

actions = []

#import conspire
#actions += conspire.tests(folder_path)

import reckon_paper
actions += reckon_paper.tests(folder_path)

# Shuffle to isolate ordering effects
rng.shuffle(actions)

bar = '##################################################'

total = len(actions)
for i, act in enumerate(actions):
    print(bar, flush=True)
    print(f"TEST-{i} out of {total}, {total - i} remaining", flush=True)
    print(bar, flush=True)
    act()

print(bar, flush=True)
print(f"TESTING DONE", flush=True)
print(bar, flush=True)
