import random
import string

for i in range(12):
    print(''.join(random.choices(string.ascii_letters, k=20)))