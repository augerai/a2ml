from functools import wraps
import sys

from .exceptions import (AugerException, NotAuthenticatedException)


def error_handler(decorated):
    def wrapper(self, *args, **kwargs):
        try:
            return decorated(self, *args, **kwargs)
        except Exception as exc:
            if self.ctx.debug:
                import traceback
                traceback.print_exc()
            self.ctx.log(str(exc))
            if not hasattr(self.ctx, 'not_reraise_exceptions')\
               or not self.ctx.not_reraise_exceptions:
                raise exc
    return wrapper


def authenticated(decorated):
    def wrapper(self, *args, **kwargs):
        # verify avalability of auger credentials
        try:
            self.ctx.credentials.verify()
        except NotAuthenticatedException as e:
            raise e
        return decorated(self, *args, **kwargs)
    return wrapper

def _get_project(self, autocreate):
    from .project import Project

    project_name = self.ctx.config.get('name', None)
    if project_name is None:
        raise AugerException(
            'Please specify project name in auger.yaml/name...')
    project = Project(self.ctx, project_name)
    project_properties = project.properties()
    if project_properties is None:
        if autocreate:
            self.ctx.log(
                'Can\'t find project %s on the Auger Cloud. '
                'Creating...' % project_name)
            project.create()
        else:
            raise AugerException('Can\'t find project %s' % project_name)
    return project

def with_project(autocreate=False):
    def decorator(decorated):
        @wraps(decorated)
        def wrapper(self, *args, **kwargs):
            project = _get_project(self, autocreate)
            return decorated(self, project, *args, **kwargs)
        return wrapper
    return decorator

def with_dataset(decorated):
    from .dataset import DataSet

    def wrapper(self, *args, **kwargs):
        project = _get_project(self, False)
        data_set_name = self.ctx.config.get('dataset', None)
        if data_set_name is None:
            raise AugerException(
                'Please specify dataset name in auger.yaml/dataset...')
        dataset = DataSet(self.ctx, project, data_set_name)
        return decorated(self, dataset, *args, **kwargs)
    return wrapper
