import argparse 
import os
import csv
from google.cloud import automl_v1beta1 as automl
from google.cloud.automl_v1beta1 import enums
# if using A2ML with Google Cloud AutoML tables then
# insure that your GOOGLE_APPLICATION_CREDENTIALS environment variable 
# points to the application credentials file given from your Google Cloud SDK
# you can also set a default PROJECT_ID for Google Cloud in your environment
import abc
from abc import ABC, abstractmethod 
class Model:
    def predict(self):
        pass
    def review(self):
        pass
    def evaluate(self):
        pass
    def deploy(self):
        pass
    def import_data(self,source):
        pass
    def config(self,target,excluded,budget):
        pass
    def train(self):
        pass

# TODO: implement these for Auger
class AugerModel(Model):  
    def __init__(self):
        pass      
    def predict(self,filepath,score_threshold):
        pass
    def review(self):
        pass
    def evaluate(self):
        pass
    def deploy(self):
        pass
    def import_data(self):
        pass
    def config(self):
        pass
    def train(self):
        pass

class GCModel(Model):
    def __init__(self,project_id,compute_region):
        self.client = automl.AutoMlClient()
        self.project_id = project_id
        self.compute_region = compute_region 
        self.project_location = self.client.location_path(project_id,self.compute_region)

    def import_data(self,source,name): 
        self.name = name 
        create_dataset_response = self.client.create_dataset(
            self.project_location,
            {'display_name': self.name,
            'tables_dataset_metadata': {}})
        self.dataset_id = create_dataset_response.name
        self.dataset_full_id = self.client.dataset_path(self.project_id, self.compute_region, self.dataset_id)
        self.dataset_name = self.client.dataset_path(self.project_id, self.compute_region, self.dataset_id)
        print('Created dataset: {}'.format(self.dataset_id))
        print('Full ID: {}'.format(self.dataset_full_id))

        if source.startswith('bq'):
            input_config = {"bigquery_source": {"input_uri": source}}
        else:
            # Get the multiple Google Cloud Storage URIs.
            input_uris = source.split(",")
            input_config = {"gcs_source": {"input_uris": input_uris}}

        print("Processing import: {}".format(self.dataset_id))
        operation= self.client.import_data(self.dataset_id, input_config)
        # synchronous check of operation status.
        import_data_response = operation.result()
        print("Imported data: {}".format(import_data_response))
        return self.dataset_id

    def config(self,target,excluded,budget,metric):
        self.target = target
        self.excluded = excluded
        self.budget = budget
        self.dataset_name = self.client.dataset_path(self.project_id, self.compute_region, self.dataset_id)

        list_table_specs_response = self.client.list_table_specs(self.dataset_name)

        table_specs = [s for s in list_table_specs_response]

        table_spec_name = table_specs[0].name
        list_column_specs_response = self.client.list_column_specs(table_spec_name)
        self.column_specs = {s.display_name: s for s in list_column_specs_response}

        label_column_name = target
        label_column_spec = self.column_specs[label_column_name]
        label_column_id = label_column_spec.name.rsplit('/', 1)[-1]
        update_dataset_dict = {
            'name': self.dataset_name, 
            'tables_dataset_metadata': {'target_column_spec_id': label_column_id}}
        update_dataset_response = self.client.update_dataset(update_dataset_dict)
        print("Updated dataset response: {}".format(update_dataset_response))
        self.feat_list = list(self.column_specs.keys())
        self.feat_list.remove(target)
        for exclude in excluded:
            self.feat_list.remove(exclude)
        self.budget = budget
        self.metric = metric
    
    def train(self):
        print("Training model: {}".format(self.name))
        model_dict = {
        'display_name': self.name,
        'dataset_id': self.dataset_name.rsplit('/', 1)[-1],
        'tables_model_metadata': {
            'target_column_spec': self.column_specs[self.target],
            'input_feature_column_specs': [
                self.column_specs[x] for x in self.feat_list],
            'train_budget_milli_node_hours': self.budget,
            'optimization_objective': self.metric}}
        response = self.client.create_model(self.project_location,model_dict)
        op_name = response.operation.name
        print("Training operation name: {}".format(op_name))
        self.id =op_name.rsplit('/', 1)[-1]
        self.full_id = self.client.model_path(self.project_id, self.compute_region, self.id)
        print("Model ID: {}".format(self.id))

        # dont wait for full training now: just let people query later
        #model_response=response.result()
        #metadata = model_response.metadata()
        #print("Training completed: {}".format(metadata))

    def evaluate(self):
        self.full_id = self.client.model_path(self.project_id, self.compute_region, self.id)
        # List all the model evaluations in the model by applying filter.
        response = self.client.list_model_evaluations(self.full_id)
        print("List of model evaluations:")
        for evaluation in response:
            print("Model evaluation name: {}".format(evaluation.name))
            print("Model evaluation id: {}".format(evaluation.name.split("/")[-1]))
            print("Model evaluation example count: {}".format(
                evaluation.evaluated_example_count))
            print("Model evaluation time:")
            print("\tseconds: {}".format(evaluation.create_time.seconds))
            print("\tnanos: {}".format(evaluation.create_time.nanos))
            print("\tevaluation:{}",evaluation
                )
            print("\n")

    # TODO: handle already deployed model exception (400)
    def deploy(self):
        self.full_id = self.client.model_path(self.project_id, self.compute_region, self.id)
        response = self.client.deploy_model(self.full_id)
        print("Model deployed:{}".format(response))

    def predict(self,file_path,score_threshold):
        self.full_id = self.client.model_path(self.project_id, self.compute_region, self.id)
        prediction_client = automl.PredictionServiceClient()
        predictions_file = file_path.split('.')[0]+'_results.csv' 
        predictions=open(predictions_file, "wt")  
        with open(file_path,"rt") as csv_file:
            # Read each row of csv
            content = csv.reader(csv_file)

            csvlist = ''
            for row in content:
                # Create payload
                values = []
                for column in row:
                    print("Column: {}".format(column))
                    values.append({'number_value': float(column)})
                csvlist=",".join(row)
                print ("CSVList: {}".format(csvlist))
                payload = {
                    'row': {'values': values}
                }
                response = prediction_client.predict(self.full_id, payload)
                print("Prediction results:")
                for result in response.payload:
                    if (result.classification.score >= score_threshold): 
                        prediction=result.tables.value.number_value
                print("Prediction: {}".format(prediction))
                csvlist += (',' + str(prediction) + '\n')
                predictions.write(csvlist)   

    def review(self):
        # Get the full path of the model.
        self.full_id = self.client.model_path(self.project_id, self.compute_region, self.id)

        # Get complete detail of the model.
        model = self.client.get_model(self.full_id)

        # Retrieve deployment state.
        if model.deployment_state == enums.Model.DeploymentState.DEPLOYED:
            deployment_state = "deployed"
        else:
            deployment_state = "undeployed"

        # Display the model information.
        print("Model name: {}".format(model.name))
        print("Model id: {}".format(model.name.split("/")[-1]))
        print("Model display name: {}".format(model.display_name))
        print("Model metadata:")
        print(model.tables_model_metadata)
        print("Model create time:")
        print("\tseconds: {}".format(model.create_time.seconds))
        print("\tnanos: {}".format(model.create_time.nanos))
        print("Model deployment state: {}".format(deployment_state))  
