import sys
from time import time

n = 0
start = time()
try:
    for line in sys.stdin:
        n += 1
except KeyboardInterrupt:
    pass
end = time()

print(f"{n} lines in {round(end - start)} seconds -> {round(n / (end - start))}/s")
