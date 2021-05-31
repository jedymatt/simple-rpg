import random


def random_dice():
    return random.choices([1, 2, 3, 4, 5, 6], weights=[.07, .23, .40, .20, .09, .01])[0]
