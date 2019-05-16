import os
import shutil

class Template(object):

    @staticmethod
    def copy(experiment_path, provider):
        module_path = os.path.dirname(os.path.abspath(__file__))
        default_config = os.path.abspath(os.path.join(
            module_path, '../template/%s.yaml' % provider))
        config_name = os.path.join(experiment_path, 'config.yaml')
        shutil.copy2(default_config, config_name)
