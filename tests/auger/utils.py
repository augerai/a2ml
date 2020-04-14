from a2ml.api.auger.impl.cloud.rest_api import RestApi


ORGANIZATIONS = {
    'meta': {
        'status': 200,
        'pagination':
            {'limit': 100, 'total': 1, 'count': 1, 'offset': 0}
    },
    'data': [{'name': 'auger'}]
}

PROJECT_FILE = {
    'data': {
        'name': 'iris.csv',
        'id': 1256,
        'statistics': {
            'columns_count': 5, 'count': 150,
            'stat_data': [
            {
                'datatype': 'categorical',
                'column_name': 'species',
                'unique_values': 3
            },{
                'datatype': 'integer',
                'column_name': 'sepal_length'
            },{
                'datatype': 'integer',
                'column_name': 'sepal_width'
            },{
                'datatype': 'integer',
                'column_name': 'petal_length'
            },{
                'datatype': 'integer',
                'column_name': 'petal_width'
            }]
         },
    }
}

PROJECT_FILES = {
    'meta': {
        'pagination': {'offset': 0, 'count': 1, 'total': 1, 'limit': 100},
        'status': 200},
    'data': [PROJECT_FILE['data']]
}

EXPERIMENT = {
    'data': {
        'name': 'iris-1.csv-experiment',
        'project_file_id': 1256,
    }
}

EXPERIMENTS = {
    'meta': {
        'pagination': {'offset': 0, 'count': 1, 'total': 1, 'limit': 100},
        'status': 200},
    'data': [EXPERIMENT['data']]
}

PROJECTS = {
    'meta': {
        'status': 200,
        'pagination': {
            'count': 2, 'limit': 100, 'offset': 0, 'total': 2}},
    'data': [
        {"id": 2, "name": "project_1"},
        {"id": 1, "name": "cli-integration-test"}]
}

PAYLOAD_DEFAULT = {
    'get_organizations': ORGANIZATIONS,
    'get_projects': PROJECTS,
    'get_project_files': {
        'meta': {
            'status': 200,
            'pagination': {
                'count': 2, 'offset': 0, 'total': 2, 'limit': 100}
        },
        'data': [
        {'id': 1, 'name': 'test_dataset1'},
        {'id': 2, 'name': 'test_dataset2'}
        ],
    }
}

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

