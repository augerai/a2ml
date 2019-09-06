from auger.api.cloud.rest_api import RestApi


def interceptor(payload, monkeypatch):
    def payloader(x, method, *args, **kwargs):
        return payload[method]
    monkeypatch.setattr(
        RestApi, 'call_ex', payloader)


def object_status_chain(statuses, monkeypatch):
    current = statuses.pop(0)
    if len(statuses):
        monkeypatch.setattr(
            RestApi, 'wait_for_object_status', lambda x, *a, **kw: current)
    return current
