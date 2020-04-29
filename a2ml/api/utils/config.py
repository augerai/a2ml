import os
import logging
import ruamel.yaml

from a2ml.api.utils.config_yaml import ConfigYaml
from a2ml.api.utils import fsclient

log = logging.getLogger("a2ml")

'''Config to serialize pass to server side deserialize, then pass back and save on CLI side'''
class SerializableConfigYaml(ConfigYaml):
    def __getstate__(self):
        return {
            'filename': self.filename,
            'yaml': ruamel.yaml.dump(self.yaml, Dumper=ruamel.yaml.RoundTripDumper)
        }

    def __setstate__(self, state):
        self.filename = state['filename']
        self.yaml = ruamel.yaml.load(state['yaml'], Loader=ruamel.yaml.RoundTripLoader)

    def write(self, filename=None, client_side=True):
        if client_side:
            super().write(filename)


class ConfigParts(object):
    def __init__(self):
        self.parts = {}
        self.part_names = ['config', 'auger', 'azure', 'google']
        self.is_loaded = False

    def load(self, path=None):
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

    def __init__(self, name='config', path=None):
        super(Config, self).__init__()
        self.runs_on_server = False
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

    def get_list(self, path, default=None):
        data = self.get(path, default)
        res = data

        if data:
            if isinstance(data, str):
                res = data.split(",")
                res = [item.strip() for item in res]
            else:
                res = list(data)

        return res
               
    def get_path(self):
        path = self.path
        if path is None:
            path = os.getcwd()

        return path

    def set(self, part_name, path, value):
        if (part_name == 'config' and self.ismultipart()):
            self.parts.part('config').set(path, value)
        else:
            self.parts.part(self.name).set(path, value)

    def write(self, part_name):
        if (part_name == 'config' and self.ismultipart()):
            self.parts.part('config').write(client_side=not self.runs_on_server)
        else:
            self.parts.part(self.name).write(client_side=not self.runs_on_server)

    def write_all(self):
        for part_name in self.parts.parts.keys():
            self.write(part_name)

    def ismultipart(self):
        return self.parts.ismultipart()

    def load(self, path=None, reload=False):
        if (not self.parts.is_loaded) or reload:
            self.parts.load(path)
        return self
