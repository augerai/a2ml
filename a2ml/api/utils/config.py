import os
import logging

from auger.api.utils.config_yaml import ConfigYaml

log = logging.getLogger("a2ml")

class ConfigParts(object):
    parts = {}
    part_names = ['config', 'auger', 'azure', 'google']
    is_loaded = False

    @classmethod
    def load(cls, path = None):
        if path is None:
            path = os.getcwd()
        for pname in ConfigParts.part_names:
            filename = os.path.abspath(os.path.join(path, '%s.yaml' % pname))
            if os.path.isfile(filename):
                ConfigParts.parts[pname] = ConfigParts._load(filename)
        ConfigParts.is_loaded = True

    @classmethod
    def ismultipart(cls):
        return(len(ConfigParts.parts.keys()) > 1)

    @classmethod
    def keys(cls):
        return ConfigParts.parts.keys()

    @classmethod
    def part(cls, name):
        return ConfigParts.parts[name]

    @classmethod
    def _load(cls, name):
        part = ConfigYaml()
        if os.path.isfile(name):
            part.load_from_file(name)
        return part

class Config(object):

    def __init__(self, name = 'config'):
        super(Config, self).__init__()
        self.name = name
        self.path = None
        self.parts = ConfigParts()
        self.load()

    def get(self, path, default=None):
        if len(self.parts.keys()) == 0:
            return default
        if 'config' in self.parts.keys():
            default = self.parts.part('config').get(path, default)
        return self.parts.part(self.name).get(path, default)

    def set(self, part_name, path, value):
        if (part_name == 'config' and self.ismultipart()):
            self.parts.part('config').set(path, value)
        else:
            self.parts.part(self.name).set(path, value)

    def write(self, part_name):
        if (part_name == 'config' and self.ismultipart()):
            self.parts.part('config').write()
        else:
            self.parts.part(self.name).write()

    def ismultipart(self):
        return self.parts.ismultipart()

    def load(self, path = None, reload = False):
        if (not ConfigParts.is_loaded) or reload:
            ConfigParts.load(path)
        return self
