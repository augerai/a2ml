import os
import logging
import ruamel.yaml

from auger.api.utils.config_yaml import ConfigYaml
from auger.api.utils import fsclient

log = logging.getLogger("a2ml")


class SerializableConfigYaml(ConfigYaml):
    def __getstate__(self):
        return {'yaml': ruamel.yaml.dump(self.yaml, Dumper=ruamel.yaml.RoundTripDumper)}

    def __setstate__(self, state):
        self.yaml = ruamel.yaml.load(state['yaml'], Loader=ruamel.yaml.RoundTripLoader)


class ConfigParts(object):
    def __init__(self):
        self.parts = {}
        self.part_names = ['config', 'auger', 'azure', 'google']
        self.is_loaded = False

    def load(self, path = None):
        if path is None:
            path = os.getcwd()
        for pname in self.part_names:
            filename = os.path.join(path, '%s.yaml' % pname)

            if not fsclient.is_s3_path(filename):
                filename = os.path.abspath(filename)

            if fsclient.is_file_exists(filename):
                self.parts[pname] = self._load(filename)
        self.is_loaded = True

    def ismultipart(self):
        return(len(self.parts.keys()) > 1)

    def keys(self):
        return self.parts.keys()

    def part(self, name):
        return self.parts[name]

    def _load(self, name):
        part = SerializableConfigYaml()
        if fsclient.is_file_exists(name):
            part.load_from_file(name)
        return part

class Config(object):

    def __init__(self, name = 'config', path=None):
        super(Config, self).__init__()
        self.name = name
        self.path = path
        self.parts = ConfigParts()
        self.load(path)

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
        if (not self.parts.is_loaded) or reload:
            self.parts.load(path)
        return self
