import random

msg = "a"
dots_amount = random.randint(3, 10)
for i in range(1, dots_amount):
    print(msg + "." * i)