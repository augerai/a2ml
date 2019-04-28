import argparse 
import os
from google.cloud import automl_v1beta1 as automl
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

def train_model(client,project_id,project_location,dataset_name,target,model_name,training_budget):
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
    
    model_dict = {
    'display_name': model_name,
    'dataset_id': dataset_name.rsplit('/', 1)[-1],
    'tables_model_metadata': {
        'target_column_spec': column_specs[target],
        'input_feature_column_specs': [
            column_specs[x] for x in feat_list],
        'train_budget_milli_node_hours': training_budget,
        'optimization_objective': 'MINIMIZE_MAE'}}

    print(:"Training model: {}".format(model_name))
    operation = client.create_model(project_location, model_dict)
    model_response = operation.result()

    # Handle metadata.
    metadata = model_response.metadata()
    print("Model creation response: {}".format(metadata))
    return metadata

def main():

    client = automl.AutoMlClient()

    parser = argparse.ArgumentParser(description='Automate AutoML Pipeline.')
    parser.add_argument('-p','--project',help='Google Cloud project ID')
    parser.add_argument('-d','--dataset',help='Google Cloud dataset ID')
    parser.add_argument('-m','--model',help='Model name')
    parser.add_argument('-s','--source',help='Source path for loading dataset')
    parser.add_argument('-t','--target',help='Target column from dataset')
    parser.add_argument('-b','--budget',type=int, help='Training time in seconds')
    parser.add_argument('-i','--import_first',help='Perform import before training')
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
    
    project_location = client.location_path(project_id,"us-central1")
    if (args.import_first): 
        dataset_name=import_data(client,project_id, project_location,model_name,source)
    train_model(client,project_id,project_location,dataset_name,target,model_name,training_budget)

if __name__ == '__main__':
    main()