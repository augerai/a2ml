from .cloud.project import AugerProjectApi
from .cloud.org import AugerOrganizationApi

from ..credentials import Credentials


class Project(AugerProjectApi):
    """Auger Cloud Projects(s) management"""

    def __init__(self, ctx, project_name=None, project_id=None):
        credentials = Credentials(ctx).load()

        org = AugerOrganizationApi(ctx, credentials.organization)
        super(Project, self).__init__(ctx, org, project_name, project_id)
