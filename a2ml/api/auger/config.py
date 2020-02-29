class AugerConfig(object):
    """Modify configuration options in auger.yaml."""

    def __init__(self, ctx):
        super(AugerConfig, self).__init__()
        self.ctx = ctx

    def _with_auger_config(decorated):
        def wrapper(self, *args, **kwargs) :
            decorated(self, self.ctx.config, *args, **kwargs)
            self.ctx.config.write('auger')
        return wrapper

    @_with_auger_config
    def config(self, config, *args, **kwargs):
        config.set('auger', 'experiment/name',
            kwargs.get('experiment_name', ''))
        config.set('auger', 'dataset',
            kwargs.get('data_set_name', ''))
        config.set('auger', 'experiment/experiment_session_id',
            kwargs.get('experiment_session_id', ''))
        # model_type = kwargs.get('model_type', None)
        # if model_type:
        #     yaml['experiment']['metric'] = \
        #         'f1_macro' if model_type == 'classification' else 'r2'

    @_with_auger_config
    def set_data_set(self, config, data_set_name):
        config.set('auger', 'dataset', data_set_name)

    @_with_auger_config
    def set_experiment(self, config, experiment_name, experiment_session_id):
        config.set('auger', 'experiment/name', experiment_name)
        config.set('auger', 'experiment/experiment_session_id',
            experiment_session_id)
