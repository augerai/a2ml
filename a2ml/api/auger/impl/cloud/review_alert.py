from .base import AugerBaseApi
from ..exceptions import AugerException


class AugerReviewAlertApi(AugerBaseApi):
    """Auger Review Alert API."""

    def __init__(self, ctx, endpoint_api, alert_id=None):
        super(AugerReviewAlertApi, self).__init__(ctx, endpoint_api, None, alert_id)

    def create(self, params):
        return self._call_create(params)

    def create_update(self, parameters=None):
        alerts = self.list()

        config = self.ctx.config
        if not parameters:
            parameters = {}

        params = {
            'endpoint_id': self.parent_api.object_id,
            'active': parameters.get('active', config.get('review/alert/active')),
            'kind': parameters.get('type', config.get('review/alert/type')),
            'threshold': float(parameters.get('threshold', config.get('review/alert/threshold'))),
            'threshold_policy': parameters.get('threshold_policy', config.get('review/alert/threshold_policy')),
            'sensitivity': int(parameters.get('sensitivity', config.get('review/alert/sensitivity'))),
            'actions': parameters.get('action', config.get('review/alert/action')),
            'notifications': parameters.get('notification', config.get('review/alert/notification'))
        }

        if params['actions'] == 'no':
            params['actions'] = 'no_actions'
        if params['notifications'] == 'no':
            params['notifications'] = 'no_notifications'

        if not alerts:
            res = self.create(params)
        else:
            params_changed = {}
            for key, value in params.items():
                alert_value = alerts[0].get(key)
                if value is not None and value != alert_value:
                    params_changed[key] = value

            if params_changed:
                params_changed['id'] = alerts[0].get('id')
                self._call_update(params_changed)
