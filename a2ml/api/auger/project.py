from .impl.project import Project
from .impl.exceptions import AugerException
from a2ml.api.utils.decorators import error_handler, authenticated
from .impl.cloud.rest_api import RestApi
from .credentials import Credentials
from .config import AugerConfig


class AugerProject(object):

    def __init__(self, ctx):
        self.ctx = ctx
        self.credentials = Credentials(ctx).load()
        self.ctx.rest_api = RestApi(
            self.credentials.api_url, self.credentials.token)

    @error_handler
    @authenticated
    def list(self):
        count = 0
        for project in iter(Project(self.ctx).list()):
            self.ctx.log(project.get('name'))
            count += 1
        self.ctx.log('%s Project(s) listed' % str(count))
        return {'projects': Project(self.ctx).list()}

    @error_handler
    @authenticated
    def create(self, name):
        old_name, name, project = self._setup_op(name, False)
        project.create()
        if name != old_name:
            self._set_project_config(name)
        self.ctx.log('Created Project %s' % name)
        return {'created': name}

    @error_handler
    @authenticated
    def delete(self, name):
        old_name, name, project = self._setup_op(name)
        project.delete()
        if name == old_name:
            self._set_project_config(None)
        self.ctx.log('Deleted Project %s' % name)
        return {'deleted': name}

    @error_handler
    @authenticated
    def start(self, name):
        old_name, name, project = self._setup_op(name)
        if not project.is_running():
            self.ctx.log('Starting Project...')
            project.start()
            self.ctx.log('Started Project %s' % name)
        else:
            self.ctx.log('Project is already running...')
        return {'running': name}

    @error_handler
    @authenticated
    def stop(self, name):
        old_name, name, project = self._setup_op(name)
        if project.is_running():
            self.ctx.log('Stopping Project...')
            project.stop()
            self.ctx.log('Stopped Project %s' % name)
        else:
            self.ctx.log('Project is not running...')
        return {'stopped': name}

    @error_handler
    @authenticated
    def select(self, name):
        old_name, name, project = self._setup_op(name, False)
        if name != old_name:
            self._set_project_config(name)
        self.ctx.log('Selected Project %s' % name)
        return {'selected': name}

    def _set_project_config(self, name):
        AugerConfig(self.ctx).\
            set_project(name).\
            set_data_set(None).\
            set_experiment(None, None)

    def _setup_op(self, name, verify_project=True):
        old_name = self.ctx.config.get('name', None)
        if name is None:
            name = old_name
        if name is None:
            raise AugerException('Please specify Project name...')

        project = Project(self.ctx, name)

        if verify_project and not project.is_exists:
            raise AugerException('Project %s doesn\'t exists...' % name)

        return old_name, name, project
