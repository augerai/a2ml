from .base import AugerBaseApi
from ..exceptions import AugerException
from .review_alert_item import AugerReviewAlertItemApi
from .review_alert import AugerReviewAlertApi
from .user import AugerUserApi
from ...credentials import Credentials


class AugerEndpointApi(AugerBaseApi):
    """Auger Endpoint API."""

    def __init__(self, ctx, experiment_api, endpoint_id=None):
        super(AugerEndpointApi, self).__init__(
            ctx, experiment_api, None, endpoint_id)

    def create(self, pipeline_id):
        return self._call_create({'pipeline_id': pipeline_id},[])

    def create_update_alert(self):
        alert_api = AugerReviewAlertApi(self.ctx, self)
        alert_items = alert_api.list()

        config = self.ctx.config
        params = {
            'endpoint_id': self.object_id,
            'kind': config.get('review/type'),
            'threshold': float(config.get('review/threshold')),
            'sensitivity': int(config.get('review/sensitivity')),
            'actions': config.get('review/action'),
            'notifications': config.get('review/notification')
        }

        params['active'] = params['actions'] != 'no' or params['notifications'] != 'no'
        if not alert_items:
            res = alert_api.create(params)
        else:
            params_changed = {}
            for key, value in params.items():
                alert_value = alert_items[0].get(key)
                if value is not None and value != alert_value:
                    params_changed[key] = value

            if params_changed:
                params_changed['id'] = alert_items[0].get('id')
                AugerReviewAlertApi(self.ctx, self)._call_update(params_changed)
