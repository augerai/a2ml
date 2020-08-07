import os
import sys
import click
import logging
from .config import Config
import warnings

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
        self.notificator = None
        self.request_id = None
        self.provider_info = None

        if len(self.name) > 0:
            self.name = "{:<9}".format('[%s]' % self.name)
        self.debug = self.config.get('debug', debug)
        self.set_runs_on_server(False)

        def warn(*args, **kwargs):
            self.system_warning(*args, **kwargs)

        warnings.warn = warn

    def set_runs_on_server(self, value):
        self._runs_on_server = value
        self.config.runs_on_server = value

    def is_runs_on_server(self):
        return self._runs_on_server
            
    def use_auger_cloud(self):
        return self.config.get('use_auger_cloud', self.config.get('use_a2ml_hub', False))

    def get_name(self):
        return self.config.name

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

    def get_model_provider(self, model_id):
        if not model_id:
            return None
            
        if model_id.startswith("AutoML_"):
            return "azure"

        return "auger"

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
        new.set_runs_on_server(self._runs_on_server)
        new.notificator = self.notificator
        new.request_id = self.request_id
        new.config.parts = self.config.parts
        new.config.parts_changes = self.config.parts_changes

        try:
            new.config.set("providers", name, config_name='config')
        except Exception as e:
            # In case if command run in folder without config, do not set it
            pass
            
        if self._runs_on_server and hasattr(self, 'credentials'):
            new.credentials = self.credentials

        return new

    def log(self, msg, *args, **kwargs):
        log.info('%s%s' %(self.name, msg), *args, **kwargs)
        self.publish_log('info', '%s%s' %(self.name, msg), *args, **kwargs)

    def log_debug(self, msg, *args, **kwargs):
        if self.debug:
            log.debug('%s%s' %(self.name, msg), *args, **kwargs)
            self.publish_log('debug', '%s%s' %(self.name, msg), *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        log.error('%s%s' %(self.name, msg), *args, **kwargs)
        self.publish_log('error', '%s%s' %(self.name, msg), *args, **kwargs)

    def system_warning(self, *args, **kwargs):
        if self.debug and args:
            name = '[warning] '
            msg = args[0]
            log.warning('%s%s' %(name, msg))
            self.publish_log('warning', '%s%s' %(name, msg))

    def publish_log(self, level, msg, *args, **kwargs):
        if self.notificator:
            self.notificator.publish_log(self.request_id, level, msg, args, kwargs)


    @staticmethod
    def setup_logger(format='%(asctime)s %(name)s | %(message)s'):
        logging.basicConfig(
            stream=sys.stdout,
            datefmt='%H:%M:%S',
            format=format,
            level=logging.INFO)


pass_context = click.make_pass_decorator(Context, ensure=True)

