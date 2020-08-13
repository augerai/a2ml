import os
import logging
import pandas as pd
import datetime as dt
import shortuuid
import json
import re

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
        experiment_name = self._fix_experiment_name(
            self.ctx.config.get('experiment/name', dataset_name))
        # cluster_name = self._fix_cluster_name(
        #     self.ctx.config.get('cluster/name', 'cpucluster'))

        self.ctx.log("Starting search on %s Dataset..." % dataset_name)
        exclude_columns = self.ctx.config.get_list('exclude', [])
        if target in exclude_columns:
            exclude_columns.remove(target)

        project = AzureProject(self.ctx)    
        ws = project._get_ws()     
        dataset = Dataset.get_by_name(ws, dataset_name)
        if exclude_columns:
            dataset = dataset.drop_columns(exclude_columns)

        compute_target, cluster_name = self._get_compute_target(ws, project)
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

                training_data_columns = AzureDataset(self.ctx, ws)._columns(dataset)
                training_data_columns.remove(target)

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
        if self.ctx.config.get('experiment/max_cores_per_iteration'):
            automl_settings["max_cores_per_iteration"] = self.ctx.config.get('experiment/max_cores_per_iteration')
        if self.ctx.config.get('experiment/max_concurrent_iterations'):
            automl_settings["max_concurrent_iterations"] = self.ctx.config.get('experiment/max_concurrent_iterations')

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
            model_explainability = True, #To get feature importance
            **automl_settings)

        experiment = Experiment(ws, experiment_name)
        run = experiment.submit(automl_config, show_output = False)

        self.ctx.log("Started Experiment %s search..." % experiment_name)
        self.ctx.config.set('experiment/name', experiment_name)
        self.ctx.config.set('cluster/name', cluster_name)
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
                'Please provide Run ID (experiment/run_id)...')
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
                'Please provide Run ID (experiment/run_id) to evaluate')
        experiment = Experiment(ws, experiment_name)
        run = AutoMLRun(experiment = experiment, run_id = run_id)
        leaderboard, trials_count = self._get_leaderboard(run)
        leaderboard = leaderboard.to_dict('records')
        self.ctx.log('Leaderboard for Run %s' % run_id)

        headers = []
        if leaderboard:
            headers = list(leaderboard[0].keys())[:3]
        print_table(self.ctx.log, leaderboard, headers)
        provider_status = run.get_status()
        status = self._map_provider_status(provider_status)

        result = {
            'run_id': run_id,
            'leaderboard': leaderboard,
            'trials_count': trials_count,
            'status': status,
            'provider_status': provider_status,
        }

        if status == 'error':
            result['error'] = run.properties.get('errors')
            result['error_details'] = run.get_details().get('error', {}).get('error', {}).get('message')
            self.ctx.log('Status: %s, Error: %s, Details: %s' % (
                status, result['error'], result['error_details']
            ))
            self.ctx.log_debug(run.get_details().get('error'))
        else:    
            self.ctx.log('Status: %s' % status)

        return result
            
    def _map_provider_status(self, provider_status):
        # * NotStarted - This is a temporary state client-side Run objects are in before cloud submission.
        # * Starting - The Run has started being processed in the cloud. The caller has a run ID at this point.
        # * Provisioning - Returned when on-demand compute is being created for a given job submission.
        # * Preparing - The run environment is being prepared:
        #     * docker image build
        #     * conda environment setup
        # * Queued - The job is queued in the compute target. For example, in BatchAI the job is in queued state
        #      while waiting for all the requested nodes to be ready.
        # * Running - The job started to run in the compute target.
        # * Finalizing - User code has completed and the run is in post-processing stages.
        # * CancelRequested - Cancellation has been requested for the job.
        # * Completed - The run completed successfully. This includes both the user code and run
        #     post-processing stages.
        # * Failed - The run failed. Usually the Error property on a run will provide details as to why.
        # * Canceled - Follows a cancellation request and indicates that the run is now successfully cancelled.
        # * NotResponding - For runs that have Heartbeats enabled, no heartbeat has been recently sent.


        if provider_status == 'NotStarted' or provider_status == 'Starting' or \
           provider_status == 'Provisioning' or provider_status == 'Preparing' or \
           provider_status == 'Queued':
            return "preprocess"

        if provider_status == 'Running' or provider_status == 'Finalizing':
            return "started"

        if provider_status == 'Completed':
            return "completed"

        if provider_status == 'Failed':
            return "error"

        if provider_status == 'CancelRequested' or provider_status == 'Canceled':
            return "interrupted"
                
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

    def _fix_experiment_name(self, name):
        # Experiment name must be between 1 and 255 characters long. 
        # Its first character has to be alphanumeric, and the rest may contain hyphens and underscores. 
        # No whitespace is allowed.

        name = re.sub(r'\W+', '-', name)
        name = name[:255]

        return name

    def _get_compute_target(self, ws, project):
        local_cluster = project.get_cluster_config(name=None, local_config=True, ws=ws)
        project.update_cluster_config(name=None, params=local_cluster, ws=ws,
            allow_create=not self.ctx.is_runs_on_server())

        return ws.compute_targets[local_cluster['name']], local_cluster['name']

    def _get_leaderboard(self, experiment_run):
        primary_metric = experiment_run.properties['primary_metric']
        task_type = ""
        if experiment_run.properties.get("AMLSettingsJsonString"):
            settings = json.loads(experiment_run.properties.get("AMLSettingsJsonString"))
            task_type = settings.get('task_type')

        children = list(experiment_run.get_children(recursive=True))
        leaderboard = pd.DataFrame(index=['model id', 'algorithm', 'score', 'fit_time', 'algorithm_name', 'algorithm_params', 'preprocessor', 'primary_metric', "all_scores", 'task_type'])
        goal_minimize = False
        for run in children:
            if('run_algorithm' in run.properties and 'score' in run.properties):
                if run.properties['run_preprocessor']:
                    run_algorithm = '%s,%s' % (run.properties['run_preprocessor'],
                        run.properties['run_algorithm'])
                else:
                    run_algorithm = run.properties['run_algorithm']

                algorithm_params = {}    
                if run.properties.get('pipeline_spec'):
                    pipeline_spec = json.loads(run.properties.get('pipeline_spec'))
                    for item in pipeline_spec.get('objects', []):
                        if item.get('spec_class') and item.get('spec_class') != "preproc" and \
                            not "Ensemble" in item.get('class_name', ""):
                            algorithm_params = item.get('param_kwargs')
                            break

                all_scores = run.get_metrics()
                scores_to_remove = ['confusion_matrix', 'accuracy_table', 'predicted_true', 'residuals']
                for item in scores_to_remove:
                    if item in all_scores:
                        del all_scores[item]

                leaderboard[run.id] = [run.id,
                                      run_algorithm,
                                      float(run.properties['score']),
                                      run.properties['fit_time'],
                                      run.properties['run_algorithm'],
                                      algorithm_params,
                                      run.properties['run_preprocessor'],
                                      primary_metric,
                                      all_scores,
                                      task_type
                                      ]
                if('goal' in run.properties):
                    goal_minimize = run.properties['goal'].split('_')[-1] == 'min'
                    
        leaderboard = leaderboard.T.sort_values(
            'score', ascending = goal_minimize)
        trials_count = len(leaderboard)
        leaderboard = leaderboard.head(10)
        leaderboard.rename(columns={'score':primary_metric}, inplace=True)

        return leaderboard, trials_count
