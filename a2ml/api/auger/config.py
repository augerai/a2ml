class AugerConfig(object):
    """Modify configuration options in auger.yaml."""

    def __init__(self, ctx):
        super(AugerConfig, self).__init__()
        self.ctx = ctx

    def _with_auger_config(decorated):
        def wrapper(self, *args, **kwargs) :
            res = decorated(self, *args, **kwargs)
            self.ctx.config.write('auger')

            return res
            
        return wrapper

    @_with_auger_config
    def set_data_set(self, name, source=None, validation=False):
        #config.set('auger', 'dataset', data_set_name)

        if validation:
            self.ctx.config.set('auger', 'validation_dataset', name)
        else:
            self.ctx.config.set('auger', 'dataset', name)

        if source:
            self.ctx.config.set('config', 'source', source)

        if self.ctx.config.ismultipart():
            self.ctx.config.write('config')

        return self
            
    @_with_auger_config
    def set_experiment(self, experiment_name, experiment_session_id):
        self.ctx.config.set('auger', 'experiment/name', experiment_name)
        self.ctx.config.set('auger', 'experiment/experiment_session_id',
            experiment_session_id)

    @_with_auger_config
    def set_project(self, project_name):
        self.ctx.config.set('config', 'name', project_name)
        if (self.ctx.config.ismultipart()):
            self.ctx.config.write('config')
        return self

    # @_with_auger_config
    # def config(self, config, *args, **kwargs):
    #     config.set('auger', 'experiment/name',
    #         kwargs.get('experiment_name', ''))
    #     config.set('auger', 'dataset',
    #         kwargs.get('data_set_name', ''))
    #     config.set('auger', 'experiment/experiment_session_id',
    #         kwargs.get('experiment_session_id', ''))

        # model_type = kwargs.get('model_type', None)
        # if model_type:
        #     yaml['experiment']['metric'] = \
        #         'f1_macro' if model_type == 'classification' else 'r2'

        # self.ctx.config.set('config', 'name', kwargs.get('project_name', ''))

        # self.ctx.config.set('config', 'source', kwargs.get('source', ''))
        # self.ctx.config.set('auger', 'dataset', kwargs.get('data_set_name', ''))
        # self.ctx.config.set('config', 'target', kwargs.get('target', ''))

        # self.ctx.config.set('auger', 'experiment/name',
        #     kwargs.get('experiment_name', ''))
        # model_type = kwargs.get('model_type', None)
        # if model_type:
        #     self.ctx.config.set('auger', 'experiment/metric',
        #         'f1_macro' if model_type == 'classification' else 'r2')
        # self.ctx.config.set('config', 'model_type', model_type or '')
        # if (self.ctx.config.ismultipart()):
        #     self.ctx.config.write('config')
