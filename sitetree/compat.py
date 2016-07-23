from django import VERSION


class CommandOption(object):
    """Command line option wrapper."""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


def options_getter(command_options):
    """Compatibility function to get rid of optparse in management commands after Django 1.10.

    :param tuple command_options: tuple with `CommandOption` objects.

    """
    def get_options(option_func=None):
        from optparse import make_option
        from django.core.management.base import BaseCommand

        func = option_func or make_option

        options = tuple([func(*option.args, **option.kwargs) for option in command_options])

        if option_func is None:
            if VERSION < (1, 8):
                result = BaseCommand.option_list + options
            else:
                result = []

        else:
            result = options

        return result

    return get_options
