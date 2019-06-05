from google.cloud import automl_v1beta1 as automl
from google.cloud.automl_v1beta1 import enums

class GoogleImport:
    """Import data into Google's dataset."""

    def __init__(self,ctx):
        self.client = automl.AutoMlClient()
        self.project_id = ctx.config['google'].get('project',None)
        self.compute_region = ctx.config['google'].get('region',None)
        self.project_location = self.client.location_path(self.project_id,self.compute_region)
        self.dataset_id = ctx.config['google'].get('dataset_id',None)
        self.dataset_name = ctx.config['google'].get('dataset_name',None)
        self.source = ctx.config['google'].get('source', None)
        self.name = ctx.config['config'].get('name',None)

    def import_data(self):
        print("Creating dataset for project location: {}".format(self.project_location))
        create_dataset_response = self.client.create_dataset(
            self.project_location,
            {'display_name': self.name,
            'tables_dataset_metadata': {}})
        self.dataset_id = create_dataset_response.name.split('/')[-1]
        print ("Dataset ID: {}".format(self.dataset_id))
        self.dataset_name = self.client.dataset_path(self.project_id, self.compute_region, self.dataset_id)
        print('Dataset name: {}'.format(self.dataset_name))

        if self.source.startswith('bq'):
            input_config = {"bigquery_source": {"input_uri": source}}
        else:
            # Get the multiple Google Cloud Storage URIs.
            input_uris = self.source.split(",")
            input_config = {"gcs_source": {"input_uris": input_uris}}

        print("Processing import for dataset ID: {}".format(self.dataset_id))

        operation= self.client.import_data(self.dataset_name, input_config)
        # synchronous check of operation status.
        import_data_response = operation.result()
        print("Imported data: {}".format(import_data_response))
        return self

