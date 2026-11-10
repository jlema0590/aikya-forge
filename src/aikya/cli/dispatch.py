"""Dispatch native terminal/context helpers without swallowing legacy support commands."""
from importlib import import_module
from .arguments import _default_terminal_arguments

ROUTES={'terminal':'aikya.cli.terminal','review':'aikya.review.cli',
        'context-policy':'aikya.middleware.compaction','context':'aikya.context.cli','memory':'aikya.cli.memory'}


def dispatch(arguments):
    if _default_terminal_arguments(arguments):
        return True,import_module(ROUTES['terminal']).main(arguments)
    if arguments and arguments[0] in ROUTES:
        return True,import_module(ROUTES[arguments[0]]).main(arguments[1:])
    return False,None
