import os
import sys
import click
import logging
from .config import Config

log = logging.getLogger("a2ml")

CONTEXT_SETTINGS = dict(auto_envvar_prefix='A2ML')
PROVIDERS = ['auger', 'google', 'azure']
PROVIDERS_META = '|'.join(PROVIDERS)


class Context(object):
    """The Context class provides an environment to run A2ML"""
    def __init__(self, name='config', path=None, debug=False):
        """Initializes the Context instance
        
        Args:
            name (str): The name of the config file. Default is 'config'
            path(str): The path to your config file. If the config file is in the root directory leave as None.
            debug (bool): True | False. Default is False.
        
        Returns:
            object: Context object

        Example:
            .. code-block:: python

                ctx = Context()
        """
        super(Context, self).__init__()

        self.config = Config(name=name, path=path)
        self.name = self.config.name

        if len(self.name) > 0:
            self.name = "{:<9}".format('[%s]' % self.name)
        self.debug = self.config.get('debug', debug)
        self.runs_on_server = False

    def get_providers(self, provider = None):
        """constructs Context instance

        Args:
            name (str): The name of the config file. Default is 'config'
            path(str): The path to your config file. If the config file is in the root directory leave as None.
            debug (bool): True | False. Default is False.

        Returns:
            list[str]: ['azure', 'auger']

        Examples:
            .. code-block:: python

                ctx = Context()
                ctx.get_providers()

        """
        if provider:
            providers = provider
        else:
            providers = self.config.get('providers', [])

        if isinstance(providers, (str,)):
            providers = [p.strip() for p in providers.split(',')]

        if isinstance(providers, (list,)):
            for p in providers:
                if p not in PROVIDERS:
                    raise Exception('Provider %s is not supported.' % p)
            return providers

        raise Exception('Expecting list of providers in config.yaml\providers')

    def copy(self, name):
        """creates a copy of an existing Context
        
        Args:
            name (str): The name of the config file. Default is 'config'

        Returns:
            object: Context object

        Example:
            .. code-block:: python

                ctx = Context()
                new_ctx = ctx.copy()
        """
        new = Context(name, self.config.path, self.debug)
        new.runs_on_server = self.runs_on_server
        return new

    def log(self, msg, *args, **kwargs):
        log.info('%s%s' %(self.name, msg), *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        log.debug('%s%s' %(self.name, msg), *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        log.error('%s%s' %(self.name, msg), *args, **kwargs)

    @staticmethod
    def setup_logger(format='%(asctime)s %(name)s | %(message)s'):
        logging.basicConfig(
            stream=sys.stdout,
            datefmt='%H:%M:%S',
            format=format,
            level=logging.INFO)


pass_context = click.make_pass_decorator(Context, ensure=True)
