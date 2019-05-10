import os
import shutil

class Template(object):

    @staticmethod
    def copy(app_path):
        module_path = os.path.dirname(os.path.abspath(__file__))
        default_config = os.path.abspath(os.path.join(
            module_path, '../template/config.yaml'))
        shutil.copy2(default_config, app_path)
