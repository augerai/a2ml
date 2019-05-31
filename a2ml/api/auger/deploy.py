from a2ml.api.auger.base import AugerBase
from a2ml.api.auger.hub.utils.exception import AugerException
from a2ml.api.auger.hub.pipeline import AugerPipelineApi


class AugerDeploy(AugerBase):
    """Deploy you Model on Auger."""

    def __init__(self, ctx):
        super(AugerDeploy, self).__init__(ctx)

    @AugerBase._error_handler
    def deploy(self, model_id):
        # verify avalability of auger credentials
        self.credentials.verify()

        self.ctx.log('Deploying model %s' % model_id)

        self.start_project()

        pipeline_properties = AugerPipelineApi(None).create(model_id)

        self.ctx.log('Deployed model as Auger pipeline %s' % \
            pipeline_properties.get('id'))
