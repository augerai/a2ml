from google.cloud import automl_v1beta1 as automl
from google.cloud.automl_v1beta1 import enums
from a2ml.cmdl.utils.config_yaml import ConfigYaml

class GooglePredict:
    def __init__(self,ctx):
        self.client = automl.AutoMlClient()
        self.ctx=ctx
        self.project_id = ctx.config['google'].get('project',None)
        self.compute_region = ctx.config['google'].get('region',None)
        self.project_location = self.client.location_path(self.project_id,self.compute_region)
        self.dataset_id = ctx.config['google'].get('dataset_id',None)
        self.dataset_name = ctx.config['google'].get('dataset_name',None)
        self.source = ctx.config['google'].get('source', None)
        self.name = ctx.config['config'].get('name',None)

    def predict(self):
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