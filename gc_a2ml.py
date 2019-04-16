project_id = 'automl-test-237311'
compute_region = 'us-central1'
dataset_id = 'moneyball'
path = 'gs://moneyball/baseball.csv' 
training_budget=3600

from google.cloud import automl_v1beta1 as automl

def model_callback(operation_future):
    # Handle result.
    result = operation_future.result()
    return result

client = automl.AutoMlClient()
project_location = client.location_path(project_id,"us-central1")
print('Location:{}'.format(project_location))

create_dataset_response = client.create_dataset(
    project_location,
    {'display_name': dataset_id,
    'tables_dataset_metadata': {}})
dataset_name = create_dataset_response.name
dataset_id = dataset_name.split("/"[-1])
dataset_full_id = client.dataset_path(
    project_id, compute_region, dataset_id)

if path.startswith('bq'):
    input_config = {"bigquery_source": {"input_uri": path}}
else:
    # Get the multiple Google Cloud Storage URIs.
    input_uris = path.split(",")
    input_config = {"gcs_source": {"input_uris": input_uris}}

print("Processing import...")
response = client.import_data(dataset_full_id, input_config)

# synchronous check of operation status.
print("Dataimported")


list_table_specs_response = client.list_table_specs(dataset_name)
table_specs = [s for s in list_table_specs_response]

table_spec_name = table_specs[0].name
list_column_specs_response = client.list_column_specs(table_spec_name)
column_specs = {s.display_name: s for s in list_column_specs_response}
TARGET_LABEL = 'target_monetary'
label_column_name = TARGET_LABEL
label_column_spec = column_specs[label_column_name]
label_column_id = label_column_spec.name.rsplit('/', 1)[-1]
update_dataset_dict = {
    'name': dataset_name, 
    'tables_dataset_metadata': {'target_column_spec_id': label_column_id}}

update_dataset_response = client.update_dataset(update_dataset_dict)
model_display_name = dataset_id 
model_training_budget = training_budget * 1000
model_dict = {
  'display_name': model_display_name,
  'dataset_id': dataset_name.rsplit('/',1)[-1],
  'tables_model_metadata': {
      'target_column_spec': column_specs['target_monetary'],
      'input_feature_column_specs': [
          column_specs[x] for x in feat_list],
      'train_budget_milli_node_hours': model_training_budget,
      'optimization_objective': 'MINIMIZE_MAE'}}

model = {}
model_response = client.create_model(project_location, model)
model_response.add_done_callback(model_callback)

# Handle metadata.
metadata = model_response.metadata()
