from .cloud.project import AugerProjectApi
from .cloud.org import AugerOrganizationApi


class Project(AugerProjectApi):
    """Auger Cloud Projects(s) management"""

    def __init__(self, ctx, project_name=None):
        org = AugerOrganizationApi(ctx, ctx.credentials.organization)
        super(Project, self).__init__(ctx, org, project_name)
