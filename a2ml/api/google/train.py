from google.cloud import automl_v1beta1 as automl
from google.cloud.automl_v1beta1 import enums
from a2ml.cmdl.utils.config_yaml import ConfigYaml

class GoogleTrain:
    """Train your Model on Google."""

    def __init__(self, ctx):
        self.client = automl.AutoMlClient()
        self.ctx=ctx
        self.project_id = ctx.config['google'].get('project',None)
        self.compute_region = ctx.config['google'].get('region',None)
        self.project_location = self.client.location_path(self.project_id,self.compute_region)
        self.dataset_id = ctx.config['google'].get('dataset_id',None)
        self.dataset_name = ctx.config['google'].get('dataset_name',None)
        self.source = ctx.config['google'].get('source', None)
        self.name = ctx.config['config'].get('name',None)
        self.dataset_name = self.client.dataset_path(self.project_id, self.compute_region, self.dataset_id)
        self.target = ctx.config['config'].get('target',None)
        self.exclude = ctx.config['config'].get('exclude',None)
        self.budget = ctx.config['config'].get('budget',None)
        self.metric = ctx.config['google'].get('dataset_name',None)
        if self.metric is None: 
            self.metric = "MINIMIZE_MAE"


    def train(self,synchronous=False):
        print("Training model: {}".format(self.name))
        
        print("Listing tables from: {}".format(self.dataset_name))
        list_table_specs_response = self.client.list_table_specs(self.dataset_name)
        print("List table specs response: {}".format(list_table_specs_response))
        table_specs = [s for s in list_table_specs_response]
        table_spec_name = table_specs[0].name
        print("Table spec name: {}".format(table_spec_name))
        
        list_column_specs_response = self.client.list_column_specs(table_spec_name)
        self.column_specs = {s.display_name: s for s in list_column_specs_response}

        label_column_name = self.target
        label_column_spec = self.column_specs[label_column_name]
        label_column_id = label_column_spec.name.rsplit('/', 1)[-1]
        update_dataset_dict = {
            'name': self.dataset_name, 
            'tables_dataset_metadata': {'target_column_spec_id': label_column_id}}
        update_dataset_response = self.client.update_dataset(update_dataset_dict)
        print("Updated dataset response: {}".format(update_dataset_response))
        self.feat_list = list(self.column_specs.keys())
        self.feat_list.remove(self.target)
        excluded = self.exclude.split(',')
        for exclude in excluded:
            print("Removing: {}".format(exclude))
            try: 
                self.feapwdt_list.remove(exclude)
            except:
                print("Can't find: {}".format(exclude))

        model_dict = {
        'display_name': self.name,
        'dataset_id': self.dataset_name.rsplit('/',1)[-1],
        'tables_model_metadata': {
            'target_column_spec': self.column_specs[self.target],
            'input_feature_column_specs': [
                self.column_specs[x] for x in self.feat_list],
            'train_budget_milli_node_hours': self.budget,
            'optimization_objective': self.metric}}
        response = self.client.create_model(self.project_location,model_dict)

        self.operation_name = response.operation.name
        print("Training operation name: {}".format(self.operation_name))
        self.ctx.config['google'].yaml['operation_name']=self.operation_name

        if synchronous: 
            model_response=response.result()
            metadata = model_response.metadata()
            print("Training completed: {}".format(metadata))
            model_name = model_response.name()
            print("Model name: {}".format(model_name))

        self.ctx.config['google'].write()