
import os
from a2ml.api import gc_a2ml

from google.cloud import automl_v1beta1 as automl
class TestGCModel():
    def test_import_data(self):
        source = 'gs://moneyball/baseball.csv'
        region = 'us-central1'
        name = 'moneyball'
        project_id = "automl-test-237311"
        print("Project ID: {}".format(project_id))
        model = gc_a2ml.GCModel(name,project_id,region)
        print("Testing import data for GCModel {}".format(name))
        model.import_data(source)
        assert(len(model.dataset_id)>0)

    def test_train(self):
        region = 'us-central1'
        name = 'moneyball'
        project_id = "automl-test-237311"
        model = gc_a2ml.GCModel(name,project_id,region)
        excluded = "Team,League,Year"
        budget = 3600
        metric = 'MINIMIZE_MAE'
        print("Testing config for GCModel {}".format(name))
        dataset_id = 'TBL4772768869943083008'
        update_dataset_response = model.train(dataset_id,"RS",excluded.split(','),budget,metric)
        print("Update dataset: {}",format(update_dataset_response))
        assert(model)
