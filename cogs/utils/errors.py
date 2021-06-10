from discord.ext import commands


class MaximumExpError(ValueError):
    pass


class NoDieRoll(commands.CheckFailure):
    pass


class CharacterNotFound(commands.CheckFailure):
    pass


class InvalidAmount(commands.CheckFailure):
    pass


class ItemNotFound(commands.CheckFailure):
    pass


class InsufficientAmount(commands.CheckFailure):
    pass


class InsufficientItem(commands.CheckFailure):
    pass


class ItemNotSellable(commands.CheckFailure):
    pass
