class AugerConfig(object):
    """Modify configuration options in auger.yaml."""

    def __init__(self, ctx):
        super(AugerConfig, self).__init__()
        self.ctx = ctx

    def _with_auger_yaml(decorated):
        def wrapper(self, *args, **kwargs) :
            auger_config = self.ctx.config['auger']
            decorated(self, auger_config.yaml, *args, **kwargs)
            auger_config.write()
        return wrapper

    @_with_auger_yaml
    def config(self, yaml, *args, **kwargs):
        yaml['experiment']['name'] = \
            kwargs.get('experiment_name', '')
        yaml['data_source']['name'] = \
            kwargs.get('data_source_name', '')
        yaml['experiment']['experiment_session_id'] = \
            kwargs.get('experiment_session_id', '')

        yaml['project_name'] = kwargs.get('project_name', '')
        yaml['org_name'] = kwargs.get('organisation_name', '')

        model_type = kwargs.get('model_type', None)
        if model_type:
            yaml['experiment']['metric'] = \
                'f1_macro' if model_type == 'classification' else 'r2'

    @_with_auger_yaml
    def set_organisation_name(self, yaml, name):
        yaml['org_name'] = name

    @_with_auger_yaml
    def set_data_source(self, yaml, data_source_name):
        yaml['data_source']['name'] = data_source_name

    @_with_auger_yaml
    def set_experiment(self, yaml, experiment_name, experiment_session_id):
        yaml['experiment']['name'] = experiment_name
        yaml['experiment']['experiment_session_id'] = experiment_session_id
