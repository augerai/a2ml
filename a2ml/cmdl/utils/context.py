import os
import sys
import click
import logging
from .config_yaml import ConfigYaml

log = logging.getLogger("a2ml")

CONTEXT_SETTINGS = dict(auto_envvar_prefix='A2ML')
PROVIDERS = ['auger', 'google', 'azure']
PROVIDERS_META = '|'.join(PROVIDERS)


class Context(object):

    def __init__(self, name=''):
        super(Context, self).__init__()
        self.load_config()
        if len(name) > 0:
            name = "{:<9}".format('[%s]' % name)
        self.name = name

    def copy(self, name):
        new = Context(name)
        new.config = self.config
        return new

    def log(self, msg, *args, **kwargs):
        log.info('%s%s' %(self.name, msg), *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        log.debug('%s%s' %(self.name, msg), *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        log.error('%s%s' %(self.name, msg), *args, **kwargs)

    def load_config(self, path=None):
        self.config = {}
        if path is None:
            path = os.getcwd()
        for provider in ['config'] + PROVIDERS:
            self.config[provider] = self._load_config(
                 os.path.abspath(os.path.join(path, '%s.yaml' % provider)))

    def _load_config(self, name):
        config = ConfigYaml()
        if os.path.isfile(name):
            config.load_from_file(name)
        return config

    @staticmethod
    def setup_logger(format='%(asctime)s %(name)s | %(message)s'):
        logging.basicConfig(
            stream=sys.stdout,
            datefmt='%H:%M:%S',
            format=format,
            level=logging.INFO)


pass_context = click.make_pass_decorator(Context, ensure=True)
