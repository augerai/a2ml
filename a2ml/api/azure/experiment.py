import os
import logging
import pandas as pd
import datetime as dt
import shortuuid

from azureml.core import Run
from azureml.core import Dataset
from azureml.core import Experiment
from azureml.core.compute import AmlCompute
from azureml.core.compute import ComputeTarget
from azureml.train.automl import AutoMLConfig
from azureml.train.automl.run import AutoMLRun
from azureml.automl.core.featurization import FeaturizationConfig

from .project import AzureProject
from .exceptions import AzureException
from a2ml.api.utils.decorators import error_handler, authenticated
from .credentials import Credentials
from a2ml.api.utils.formatter import print_table
from a2ml.api.azure.dataset import AzureDataset
from a2ml.api.utils import fsclient


class AzureExperiment(object):

    def __init__(self, ctx):
        super(AzureExperiment, self).__init__()
        self.ctx = ctx
        self.credentials = Credentials(self.ctx).load()

    @error_handler
    @authenticated
    def list(self):
        ws = AzureProject(self.ctx)._get_ws()
        experiments = Experiment.list(workspace=ws)
        nexperiments = len(experiments)
        experiments = [e.name for e in experiments]
        for name in experiments:
            self.ctx.log(name)
        self.ctx.log('%s Experiment(s) listed' % str(nexperiments))
        return {'experiments': experiments}

    @error_handler
    @authenticated    
    def start(self):
        model_type = self.ctx.config.get('model_type')
        if not model_type:
            raise AzureException('Please specify model type...')
        primary_metric = self.ctx.config.get(
            'experiment/metric','spearman_correlation')
        if not primary_metric:
            raise AzureException('Please specify primary metric...')
        #TODO: check if primary_metric is constent with model_type
        target = self.ctx.config.get('target')
        if not target:
            raise AzureException('Please specify target column...')

        dataset_name = self.ctx.config.get('dataset', None)
        if dataset_name is None:
            raise AzureException('Please specify Dataset name...')
        experiment_name = self._fix_name(
            self.ctx.config.get('experiment/name', dataset_name))
        cluster_name = self._fix_name(
            self.ctx.config.get('cluster/name', 'cpucluster'))

        self.ctx.log("Starting search on %s Dataset..." % dataset_name)
        exclude_columns = self.ctx.config.get_list('exclude', [])

        ws = AzureProject(self.ctx)._get_ws()     
        dataset = Dataset.get_by_name(ws, dataset_name)
        if exclude_columns:
            dataset = dataset.drop_columns(exclude_columns)

        training_data_columns = AzureDataset(self.ctx, ws)._columns(dataset)
        training_data_columns.remove(target)

        compute_target = self._get_compute_target(ws, cluster_name)

        automl_settings = {
            "iteration_timeout_minutes" : self.ctx.config.get(
                'experiment/max_eval_time',10),
            "iterations" : self.ctx.config.get(
                'experiment/max_n_trials',10),
            "primary_metric" : primary_metric,
            "verbosity" : logging.INFO,
            "enable_stack_ensemble": self.ctx.config.get(
                'experiment/use_ensemble', False)
        }

        validation_data = None
        if self.ctx.config.get('experiment/validation_source'):
            if self.ctx.config.get('experiment/validation_dataset'):
                validation_data = Dataset.get_by_name(ws, self.ctx.config.get('experiment/validation_dataset'))
            if not validation_data:
                res = AzureDataset(self.ctx).create(
                    source = self.ctx.config.get('experiment/validation_source'),
                    validation = True
                )
                validation_data = Dataset.get_by_name(ws, res['dataset']).keep_columns(training_data_columns)
        else:
            self.ctx.config.remove('experiment/validation_dataset')
            self.ctx.config.write()

            automl_settings["n_cross_validations"] = self.ctx.config.get(
                'experiment/cross_validation_folds', 5)
            if self.ctx.config.get('experiment/validation_size'):
                automl_settings["validation_size"] = self.ctx.config.get('experiment/validation_size')

        if self.ctx.config.get('experiment/max_total_time'):
            automl_settings["experiment_timeout_hours"] = float(self.ctx.config.get('experiment/max_total_time'))/60.0

        # if self.ctx.config.get('exclude'):
        #     fc = FeaturizationConfig()
        #     fc.drop_columns = self.ctx.config.get('exclude').split(",")
        #     automl_settings["featurization"] = fc

        # It should be empty folder
        snapshot_path = os.path.join(os.getcwd(), ".azureml")
        #fsclient.create_folder()
        automl_config = AutoMLConfig(
            task = model_type,
            debug_log = 'automl_errors.log',
            path = snapshot_path,
            compute_target = compute_target,
            training_data = dataset,
            validation_data = validation_data,
            label_column_name = target,
            **automl_settings)

        experiment = Experiment(ws, experiment_name)
        run = experiment.submit(automl_config, show_output = False)

        self.ctx.log("Started Experiment %s search..." % experiment_name)
        self.ctx.config.set('experiment/name', experiment_name)
        self.ctx.config.set('experiment/run_id', run.run_id)
        self.ctx.config.write()

        return {'experiment_name': experiment_name, 'run_id': run.run_id}

    @error_handler
    @authenticated    
    def stop(self, run_id = None):
        ws = AzureProject(self.ctx)._get_ws()
        experiment_name = self.ctx.config.get('experiment/name', None)
        if experiment_name is None:
            raise AzureException('Please specify Experiment name...')
        if run_id is None:
            run_id = self.ctx.config.get('experiment/run_id', None)
        if run_id is None:
            raise AzureException(
                'Pleae provide Run ID (experiment/run_id)...')
        experiment = Experiment(ws, experiment_name)
        run = AutoMLRun(experiment = experiment, run_id = run_id)
        run.cancel()
        return {'stopped': experiment_name}

    @error_handler
    @authenticated    
    def leaderboard(self, run_id = None):
        ws = AzureProject(self.ctx)._get_ws()
        experiment_name = self.ctx.config.get('experiment/name', None)
        if experiment_name is None:
            raise AzureException('Please specify Experiment name...')
        if run_id is None:
            run_id = self.ctx.config.get('experiment/run_id', None)
        if run_id is None:
            raise AzureException(
                'Pleae provide Run ID (experiment/run_id) to evaluate')
        experiment = Experiment(ws, experiment_name)
        run = AutoMLRun(experiment = experiment, run_id = run_id)
        leaderboard = self._get_leaderboard(run).to_dict('records')
        self.ctx.log('Leaderboard for Run %s' % run_id)
        print_table(self.ctx.log,leaderboard)
        status = run.get_status()
        if status == 'Failed':
            self.ctx.log('Status: %s, Error: %s, Details: %s' % (
                status, run.properties.get('errors'), run.get_details().get('error', {}).get('error', {}).get('message')
            ))
            self.ctx.log_debug(run.get_details().get('error'))
        else:    
            self.ctx.log('Status: %s' % status)

        return {
            'run_id': run_id,
            'leaderboard': leaderboard,
            'status': status }

    @error_handler 
    @authenticated       
    def get_experiment_settings(self):
        return 
                
    @error_handler 
    @authenticated       
    def history(self):
        ws = AzureProject(self.ctx)._get_ws()
        experiment_name = self.ctx.config.get('experiment/name', None)
        if experiment_name is None:
            raise AzureException('Please specify Experiment name...')
        experiment = Experiment(ws, experiment_name)
        runs = Run.list(experiment)
        result = []
        for run in runs:
            details = run.get_details()
            st = dt.datetime.strptime(
                details['startTimeUtc'], '%Y-%m-%dT%H:%M:%S.%fZ')
            et = dt.datetime.strptime(
                details['endTimeUtc'], '%Y-%m-%dT%H:%M:%S.%fZ')
            duratin = str(et-st)
            result.append({
                'id': run.id,
                'start time': details['startTimeUtc'],
                'duratin': duratin,
                'status': details['status']
            })
        print_table(self.ctx.log, result)
        return {'history': result}

    def _fix_name(self, name):
        # Name can include letters, digits and dashes.
        # It must start with a letter, end with a letter or digit,
        # and be between 2 and 16 characters in length.
        #TODO check for all conditions
        return name.replace('_','-').replace('.','-')[:16]

    def _get_compute_target(self, ws, cluster_name):
        compute_min_nodes = int(self.ctx.config.get('cluster/min_nodes',1))
        compute_max_nodes = int(self.ctx.config.get('cluster/max_nodes',4))
        compute_sku = self.ctx.config.get('cluster/type','STANDARD_D2_V2')

        if cluster_name in ws.compute_targets:
            compute_target = ws.compute_targets[cluster_name]
            if compute_target and type(compute_target) is AmlCompute:
                ct_status = compute_target.get_status()
                if ct_status:
                    ct_def = ct_status.serialize()
                    if ct_def.get('vmSize') == compute_sku and \
                       ct_def.get('scaleSettings', {}).get('minNodeCount') == compute_min_nodes and \
                       ct_def.get('scaleSettings', {}).get('maxNodeCount') == compute_max_nodes:
                        self.ctx.log(
                            'Found compute target %s ...' % cluster_name)

                        return compute_target
                    else:    
                        self.ctx.log('Delete existing AML compute context, since parameters has been modified.')
                        compute_target.delete()

                # It works versy slow, so just change name        
                # cluster_name = self._fix_name(shortuuid.uuid())
                # self.ctx.config.set('cluster/name', cluster_name)
                # self.ctx.config.write()
                try:
                    compute_target.wait_for_completion(show_output = True)
                except Exception as e:
                    self.ctx.log_debug(str(e))    

        self.ctx.log('Creating new AML compute context %s...'%cluster_name)
        provisioning_config = AmlCompute.provisioning_configuration(
            vm_size=compute_sku, min_nodes=compute_min_nodes,
            max_nodes=compute_max_nodes)
        compute_target = ComputeTarget.create(
            ws, cluster_name, provisioning_config)
        compute_target.wait_for_completion(show_output = True)

        return compute_target

    def _get_leaderboard(self, run):
        primary_metric = run.properties['primary_metric']
        children = list(run.get_children(recursive=True))
        leaderboard = pd.DataFrame(index=['model id', 'algorithm', 'score'])
        goal_minimize = False
        for run in children:
            if('run_algorithm' in run.properties and 'score' in run.properties):
                if(run.properties['run_preprocessor']):
                    run_algorithm = '%s,%s' % (run.properties['run_preprocessor'],
                        run.properties['run_algorithm'])
                else:
                    run_algorithm = run.properties['run_algorithm']
                leaderboard[run.id] = [run.id,
                                      run_algorithm,
                                      float(run.properties['score'])]
                if('goal' in run.properties):
                    goal_minimize = run.properties['goal'].split('_')[-1] == 'min'

        leaderboard = leaderboard.T.sort_values(
            'score', ascending = goal_minimize)
        leaderboard = leaderboard.head(10)
        leaderboard.rename(columns={'score':primary_metric}, inplace=True)
        return leaderboard
