class AugerConfig(object):
    def __init__(self, ctx):
        super(AugerConfig, self).__init__()
        self.ctx = ctx

    def set_data_set(self, name, source=None, validation=False, user_name=None):
        #TODO: add more providers later
        if validation:
            self.ctx.config.set('experiment/validation_dataset', name)
            if self.ctx.use_auger_cloud() and 'azure' in self.ctx.get_providers():
                self.ctx.config.set('experiment/validation_dataset', name, "azure")
        else:
            #print("set_data_set: %s"%self.ctx.use_auger_cloud())
            self.ctx.config.set('dataset', name)
            if user_name:
                self.ctx.config.set('dataset_name', user_name)
                self.ctx.config.set(f'experiments/{user_name}/dataset', self.ctx.config.get('dataset'))

            if self.ctx.use_auger_cloud() and 'azure' in self.ctx.get_providers():
                self.ctx.config.set('dataset', name, "azure")

        self.ctx.config.write_all()
        return self
            
    def set_experiment(self, experiment_name, experiment_session_id):
        self.ctx.config.set('experiment/name', experiment_name)
        self.ctx.config.set('experiment/experiment_session_id', experiment_session_id)

        if self.ctx.config.get('dataset_name'):
            dataset_name = self.ctx.config.get('dataset_name')
            self.ctx.config.set(f'experiments/{dataset_name}/experiment_name', experiment_name)
            self.ctx.config.set(f'experiments/{dataset_name}/experiment_session_id', experiment_session_id)
            self.ctx.config.set(f'experiments/{dataset_name}/dataset', self.ctx.config.get('dataset'))

        self.ctx.config.write()

    def _get_experiment_by_dataset(self):
        dataset_name = self.ctx.config.get('dataset_name')
        experiments = self.ctx.config.get('experiments', {})
        
        return experiments.get(dataset_name, {})

    def get_experiment(self):                
        return self._get_experiment_by_dataset().get('experiment_name',
            self.ctx.config.get('experiment/name'))

    def get_experiment_session(self):                
        return self._get_experiment_by_dataset().get('experiment_session_id',
            self.ctx.config.get('experiment/experiment_session_id'))

    def get_dataset(self):
        return self._get_experiment_by_dataset().get('dataset',
            self.ctx.config.get('dataset'))
            
    def set_project(self, project_name):
        self.ctx.config.set('name', project_name)
        self.ctx.config.write()
        return self

