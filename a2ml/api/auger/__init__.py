from .impl.cloud.rest_api import RestApi

# Patch request_list list because it returns generator, which is read-once
# so Celery tasks can't read result
old_request_list = RestApi.request_list

def new_request_list(*args):
    return list(old_request_list(*args))

RestApi.request_list = new_request_list
