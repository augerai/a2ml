import argparse 
import os
import csv
from google.cloud import automl_v1beta1 as automl
from google.cloud.automl_v1beta1 import enums
# if A2ML with Google Cloud AutoML tables then
# insure that your GOOGLE_APPLICATION_CREDENTIALS environment variable 
# points to the application credentials file given from your Google Cloud SDK
# you can also set a default PROJECT_ID for Google Cloud in your environment
compute_region = 'us-central1'  # Google Cloud AutoML Tables is only 'us-central1' now
training_budget=3600  # one hour of training time by default

def import_data(client,project_id,project_location,model_name,source): 

    create_dataset_response = client.create_dataset(
        project_location,
        {'display_name': model_name,
        'tables_dataset_metadata': {}})
    dataset_id = create_dataset_response.name
    dataset_full_id = client.dataset_path(project_id, compute_region, dataset_id)
    print('Created dataset: {}'.format(dataset_id))
    print('Full ID: {}'.format(dataset_full_id))

    if source.startswith('bq'):
        input_config = {"bigquery_source": {"input_uri": source}}
    else:
        # Get the multiple Google Cloud Storage URIs.
        input_uris = source.split(",")
        input_config = {"gcs_source": {"input_uris": input_uris}}

    print("Processing import: {}".format(dataset_id))
    operation= client.import_data(dataset_id, input_config)
    # synchronous check of operation status.
    import_data_response = operation.result()
    print("Imported data: {}".format(import_data_response))
    return dataset_id

def train_model(client,project_id,project_location,dataset_name,target,model_name,excluded,training_budget):
    list_table_specs_response= client.list_table_specs(dataset_name)

    table_specs = [s for s in list_table_specs_response]

    table_spec_name = table_specs[0].name
    list_column_specs_response = client.list_column_specs(table_spec_name)
    column_specs = {s.display_name: s for s in list_column_specs_response}

    label_column_name = target
    label_column_spec = column_specs[label_column_name]
    label_column_id = label_column_spec.name.rsplit('/', 1)[-1]
    update_dataset_dict = {
        'name': dataset_name, 
        'tables_dataset_metadata': {'target_column_spec_id': label_column_id}}
    update_dataset_response = client.update_dataset(update_dataset_dict)
    print("Updated dataset response: {}".format(update_dataset_response))
    feat_list = list(column_specs.keys())
    feat_list.remove(target)
    for exclude in excluded:
        feat_list.remove(exclude)
    
    model_dict = {
    'display_name': model_name,
    'dataset_id': dataset_name.rsplit('/', 1)[-1],
    'tables_model_metadata': {
        'target_column_spec': column_specs[target],
        'input_feature_column_specs': [
            column_specs[x] for x in feat_list],
        'train_budget_milli_node_hours': training_budget,
        'optimization_objective': 'MINIMIZE_MAE'}}

    print("Training model: {}".format(model_name))
    response = client.create_model(project_location, model_dict)
    op_name = response.operation.name
    print("Training operation name: {}".format(op_name))
    model_id =op_name.rsplit('/', 1)[-1]
    print("Model ID: {}".format(model_id))

    # dont wait for full training now: just let people query later
    #model_response=response.result()
    #metadata = model_response.metadata()
    #print("Training completed: {}".format(metadata))
    return model_id

def evaluate_model(client,project_id,model_id):
    # Get the full path of the model.
    model_full_id = client.model_path(project_id, compute_region, model_id)

    # List all the model evaluations in the model by applying filter.
    response = client.list_model_evaluations(model_full_id)

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

def deploy_model(client,project_id,model_id):
    client = automl.AutoMlClient()
    # Get the full path of the model.
    model_full_id = client.model_path(project_id, compute_region, model_id)
    # Deploy model
    response = client.deploy_model(model_full_id)
    print("Model deployed:{}".format(response))

def predict_from_csv(client,project_id,model_id,file_path,score_threshold):

    model_full_id = client.model_path(project_id, compute_region, model_id)

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
            response = prediction_client.predict(model_full_id, payload)
            print("Prediction results:")
            for result in response.payload:
                if (result.classification.score >= score_threshold): 
                    prediction=result.tables.value.number_value
            print("Prediction: {}".format(prediction))
            csvlist += (',' + str(prediction) + '\n')
            predictions.write(csvlist)   

def review_model(client,project_id,model_id):
    # Get the full path of the model.
    model_full_id = client.model_path(project_id, compute_region, model_id)

    # Get complete detail of the model.
    model = client.get_model(model_full_id)

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

def main():
    client = automl.AutoMlClient()

    parser = argparse.ArgumentParser(prog='GC_A2ML',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='''A2ML - Automating AutoML. 
    
    Uppercase P-R-E-D-I-C-T options run parts of the pipeline.  
    
    Lowercase options set project, dataset, model and others that span pipeline stages .''',
        epilog='''A typical usage of the PREDICT pipeline would be successive invocations with the following options:
        -- IMPORT
        -- CONFIGURE
        -- TRAIN
        -- EVALUATE
        -- DEPLOY
        -- PREDICT
        -- REVIEW''')
           
    # capital letter arguments are pipeline phases
    parser.add_argument('-P','--PREDICT',help='Predict with deployed model',action='store_true')
    parser.add_argument('-R','--REVIEW',help='Review specified model info',action='store_true')
    parser.add_argument('-E','--EVALUATE',help='Evaluate models after training',action='store_true')
    parser.add_argument('-D','--DEPLOY',help='Deploy model',action='store_true')
    parser.add_argument('-I','--IMPORT',help='Import data for training',action='store_true')
    parser.add_argument('-C','--CONFIGURE',help='Configure model options before training',action='store_true')
    parser.add_argument('-T','--TRAIN',help='Train the model',action='store_true')
    # lower case letter arguments apply to multiple phases
    parser.add_argument('-p','--project',help='Google Cloud project ID, overrides PROJECT_ID env var')
    parser.add_argument('-d','--dataset',help='Google Cloud dataset ID')
    parser.add_argument('-m','--model',help='Model display name')
    parser.add_argument('-i','--model_id',help='Model ID')
    parser.add_argument('-s','--source',help='Source path for loading dataset')
    parser.add_argument('-t','--target',help='Target column from dataset')
    parser.add_argument('-b','--budget',type=int, help='Max training time in seconds')
    parser.add_argument('-x','--exclude',help='Excludes given columns from model')
    parser.add_argument('-z','--score_threshold',help='Score threshold for prediction')

    args = parser.parse_args()
    if (args.project is not None):
        project_id = args.project
    else:  # default project read from environment
        project_id = os.getenv('PROJECT_ID')

    if (args.dataset is not None):
        dataset_id = args.dataset 
        dataset_name = client.dataset_path(project_id, compute_region, dataset_id)
    if (args.target is not None):
        target = args.target
    if (args.model is not None):
        model_name = args.model
    if (args.source is not None):
        source = args.source 
    if (args.budget is not None):
        training_budget = args.budget
    else:
        training_budget = 3600
    if (args.model_id):
        model_id = args.model_id
    if (args.score_threshold is not None):
        score_threshold = args.score_threshold
    else: 
        score_threshold = 0.0
    if (args.exclude is not None):
        excluded = args.exclude.split(',')
    
    project_location = client.location_path(project_id,"us-central1")
    if (args.IMPORT): 
        dataset_name=import_data(client,project_id, project_location,model_name,source)
    if (args.TRAIN):
        train_model(client,project_id,project_location,dataset_name,target,model_name,excluded,training_budget)
    if (args.EVALUATE):
        evaluate_model(client,project_id,model_id)
    if (args.DEPLOY):
        deploy_model(client,project_id,model_id)
    if (args.PREDICT):
        predict_from_csv(client,project_id,model_id,source,score_threshold)
    if (args.REVIEW):
        review_model(client,project_id,model_id)

if __name__ == '__main__':
    main()