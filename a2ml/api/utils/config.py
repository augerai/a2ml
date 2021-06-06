import os
import logging
import ruamel.yaml

from a2ml.api.utils.config_yaml import ConfigYaml
from a2ml.api.utils import fsclient

log = logging.getLogger("a2ml")

'''Config to serialize pass to server side deserialize, then pass back and save on CLI side'''
class SerializableConfigYaml(ConfigYaml):
    #For pickle serialization
    def __getstate__(self):
        return {
            'filename': self.filename,
            'yaml': ruamel.yaml.YAML(typ='rt').dump(self.yaml)
        }

    def __setstate__(self, state):
        self.filename = state['filename']
        self.yaml = ruamel.yaml.YAML(typ='rt').load(state['yaml'])

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

    def part(self, name, create_if_not_exist=False):
        if name not in self.parts:
            if create_if_not_exist:
                self.parts[name] = SerializableConfigYaml()
            else:
                return SerializableConfigYaml()

        return self.parts[name]

    def _load(self, name):
        part = SerializableConfigYaml()
        part.load_from_file(name)
        return part

class Config(object):

    def __init__(self, name='config', path=None):
        super(Config, self).__init__()
        self.runs_on_server = False
        self.name = name
        self.path = path
        self.parts = ConfigParts()
        self.parts_changes = ConfigParts()
        self.load(path)

    def get(self, path, default=None, config_name=None, parts=None):
        if parts is None:
            parts = self.parts
        if len(parts.keys()) == 0:
            return default
        if 'config' in parts.keys():
            default = parts.part('config').get(path, default)
        if not config_name:
            config_name = self.name

        return parts.part(config_name).get(path, default)

    def get_list(self, path, default=None, config_name=None):
        data = self.get(path, default, config_name)
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

    def get_model_path(self, model_id):
        return os.path.join(self.get_path(), 'models', model_id)

    def set(self, path, value, config_name=None):
        if not config_name:
            config_name = self.name

        self.parts.part(config_name, True).set(path, value)
        if self.runs_on_server:
            self.parts_changes.part(config_name, True).set(path, value)

    def clean_changes(self):
        self.parts_changes = ConfigParts()

    def remove(self, path, config_name=None):
        if not config_name:
            config_name = self.name

        self.parts.part(config_name).remove(path)

    def write(self, config_name=None):
        if not config_name:
            config_name = self.name

        self.parts.part(config_name).write(client_side=not self.runs_on_server)

    def write_all(self):
        for part_name in self.parts.parts.keys():
            self.write(part_name)

    def ismultipart(self):
        return self.parts.ismultipart()

    def load(self, path=None, reload=False):
        if (not self.parts.is_loaded) or reload:
            self.parts.load(path)
        return self
