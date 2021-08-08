class AugerConfig(object):
    def __init__(self, ctx):
        super(AugerConfig, self).__init__()
        self.ctx = ctx

    def set_data_set(self, name, source=None, validation=False):
        #TODO: add more providers later
        if validation:
            self.ctx.config.set('experiment/validation_dataset', name)
            if self.ctx.use_auger_cloud() and 'azure' in self.ctx.get_providers():
                self.ctx.config.set('experiment/validation_dataset', name, "azure")
        else:
            #print("set_data_set: %s"%self.ctx.use_auger_cloud())
            self.ctx.config.set('dataset', name)
            if self.ctx.use_auger_cloud() and 'azure' in self.ctx.get_providers():
                self.ctx.config.set('dataset', name, "azure")

        self.ctx.config.write_all()
        return self
            
    def set_experiment(self, experiment_name, experiment_session_id):
        self.ctx.config.set('experiment/name', experiment_name)
        self.ctx.config.set('experiment/experiment_session_id', experiment_session_id)
        self.ctx.config.write()

    def set_project(self, project_name):
        self.ctx.config.set('name', project_name)
        self.ctx.config.write()
        return self
