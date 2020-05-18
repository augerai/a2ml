class AugerConfig(object):
    def __init__(self, ctx):
        super(AugerConfig, self).__init__()
        self.ctx = ctx

    def set_data_set(self, name, source=None, validation=False):
        if validation:
            self.ctx.config.set('experiment/validation_dataset', name)
        else:
            self.ctx.config.set('dataset', name)

        self.ctx.config.write()
        return self
            
    def set_experiment(self, experiment_name, experiment_session_id):
        self.ctx.config.set('experiment/name', experiment_name)
        self.ctx.config.set('experiment/experiment_session_id', experiment_session_id)
        self.ctx.config.write()

    def set_project(self, project_name):
        self.ctx.config.set('name', project_name)
        self.ctx.config.write()
        return self
