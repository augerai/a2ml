from google.cloud import automl_v1beta1
import os

client = automl_v1beta1.AutoMlClient()
default_project ="automl-test-237311"
dataset_name="junk3"
if len(os.sys.argv)>1:
    dataset_name=os.sys.argv[1]
parent = client.location_path(default_project,"us-central1")
print("Location :"+parent)
create_dataset_response = client.create_dataset(
    location_path,
    {'display_name': dataset_display_name,
     'tables_dataset_metadata': {}})
dataset_name = create_dataset_response.name
dataset_id = dataset_name.split("/")[-1]
# Display the dataset information.
print("Dataset name: {}".format(dataset.name))
print("Dataset id: {}".format(dataset_id))
print("Dataset display name: {}".format(dataset.display_name))
print("Image classification dataset metadata:")
print("\t{}".format(dataset.image_classification_dataset_metadata))
print("Dataset example count: {}".format(dataset.example_count))
print("Dataset create time:")
print("\tseconds: {}".format(dataset.create_time.seconds))
print("\tnanos: {}".format(dataset.create_time.nanos))

