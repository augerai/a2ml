import datetime
import os
import logging
import numpy as np
import json

from a2ml.api.utils import get_uid, get_uid4, fsclient, remove_dups_from_list, sort_arrays
from a2ml.api.utils.dataframe import DataFrame
from a2ml.api.roi.calculator import Calculator as RoiCalculator

class ModelHelper(object):

    @staticmethod
    def get_root_paths():
        root_dir = os.environ.get('AUGER_ROOT_DIR', '')
        root_tmp_dir = os.environ.get('AUGER_ROOT_TMP_DIR', '')

        if os.environ.get('S3_DATA_PATH'):
            root_dir = os.path.join("s3://", os.environ.get('S3_DATA_PATH'))

            if not os.environ.get('AUGER_LOCAL_TMP_DIR'):
                os.environ["AUGER_LOCAL_TMP_DIR"] = root_tmp_dir

            root_tmp_dir = os.path.join(root_dir, 'temp')
        elif not os.environ.get('AUGER_LOCAL_TMP_DIR'):
            os.environ["AUGER_LOCAL_TMP_DIR"] = root_tmp_dir

        return root_dir, root_tmp_dir

    @staticmethod
    def get_project_path(params=None):
        if params:
            project_path = params.get('hub_info', {}).get('project_path')
            if project_path:
                return project_path

        root_dir, root_tmp_dir = ModelHelper.get_root_paths()
        return os.path.join(root_dir, os.environ.get('AUGER_PROJECT_PATH', ''))

    @staticmethod
    def get_models_path(project_path=None):
        if not project_path:
            project_path = ModelHelper.get_project_path()
        return os.path.join(project_path, "models")

    @staticmethod
    def get_model_path(model_id=None, project_path=None, params=None):
        project_path = project_path or ModelHelper.get_project_path(params)
        if project_path:
            if not model_id and params:
                model_id = params.get('hub_info', {}).get('pipeline_id')

            if model_id:
                return os.path.join(ModelHelper.get_models_path(project_path), model_id)

    @staticmethod
    def get_experiment_session_path(params):
        project_path = ModelHelper.get_project_path(params)

        if params.get('hub_info', {}).get('experiment_id') and params.get('hub_info', {}).get('experiment_session_id'):
            return os.path.join(
                project_path,
                "channels",
                params['hub_info']['experiment_id'],
                "project_runs",
                params['hub_info']['experiment_session_id']
            )

        return None

    @staticmethod
    def get_metrics_path(params):
        experiment_session_path = ModelHelper.get_experiment_session_path(params)

        if experiment_session_path:
            return os.path.join(experiment_session_path, "metrics")

        return None

    @staticmethod
    def get_metric_path(params, metric_id=None):
        if not metric_id:
            metric_id = params.get('hub_info', {}).get('pipeline_id')

        if not metric_id:
            metric_id = params.get('uid')

        metrics_path = ModelHelper.get_metrics_path(params)
        if metrics_path:
            return os.path.join(metrics_path, metric_id)

        return None

    @staticmethod
    def save_metric(metric_id, project_path, metric_name, metric_data):
        metric_path = ModelHelper.get_metric_path({'hub_info':{'project_path': project_path}}, metric_id)

        fsclient.write_json_file(os.path.join(metric_path,
            "metric_names_feature_importance.json"))

    # @staticmethod
    # def _get_score_byname(scoring):
    #     from sklearn.metrics import get_scorer
    #     from sklearn.metrics import SCORERS

    #     #TODO: below metrics does not directly map to sklearn:
    #     # Classification : weighted_accuracy, accuracy_table, balanced_accuracy, matthews_correlation,norm_macro_recall
    #     # Regression,  Time Series Forecasting:
    #     #spearman_correlation, normalized_root_mean_squared_error, normalized_mean_absolute_error
    #     scorer = None
    #     if scoring.startswith("AUC"):
    #         scorer = get_scorer("roc_auc")
    #         average = scoring.split("_")[-1]
    #         scorer._kwargs['average'] = average
    #     elif scoring.startswith("log_loss"):
    #         scorer = get_scorer("neg_log_loss")
    #     # elif scoring.startswith("matthews_correlation"):
    #     #     scorer = get_scorer("matthews_corrcoef")
    #     elif scoring.startswith("precision_score"):
    #         scorer = get_scorer("precision")
    #         average = scoring.split("_")[-1]
    #         scorer._kwargs['average'] = average
    #     elif scoring.startswith("average_precision_score"):
    #         scorer = get_scorer("average_precision")
    #         average = scoring.split("_")[-1]
    #         scorer._kwargs['average'] = average
    #     elif scoring.startswith("recall_score"):
    #         scorer = get_scorer("recall")
    #         average = scoring.split("_")[-1]
    #         scorer._kwargs['average'] = average
    #     elif scoring.startswith("norm_macro_recall"):
    #         scorer = get_scorer("recall")
    #         scorer._kwargs['average'] = "macro"
    #     elif scoring.startswith("f1_score"):
    #         scorer = get_scorer("f1")
    #         average = scoring.split("_")[-1]
    #         scorer._kwargs['average'] = average
    #     elif scoring.startswith("precision_score"):
    #         scorer = get_scorer("precision")
    #         average = scoring.split("_")[-1]
    #         scorer._kwargs['average'] = average
    #     elif scoring.startswith("spearman_correlation"):
    #         scorer = get_scorer("r2")
    #     elif scoring.startswith("r2_score"):
    #         scorer = get_scorer("r2")
    #     elif "mean_absolute_error" in scoring:
    #         scorer = get_scorer("neg_mean_absolute_error")
    #     elif "root_mean_squared" in scoring:
    #         scorer = get_scorer("mean_squared_error")
    #     elif "median_absolute_error" in scoring:
    #         scorer = get_scorer("neg_median_absolute_error")

    #     if scorer is None:
    #         scorer = get_scorer(scoring)

    #     return scorer

    @staticmethod
    def calculate_scores(options, y_test, X_test=None, estimator=None, y_pred=None, raise_main_score=True):
        from sklearn.metrics import get_scorer
        from sklearn.model_selection._validation import _score
        from sklearn.metrics import confusion_matrix

        # For calculate_scores
        from .scores.regression import spearman_correlation_score, mae_ex
        from .scores.classification import AUC_weighted_score

        import inspect

        if options.get('fold_group') == 'time_series_standard_model':
            pp_fold_groups_params = options.get('pp_fold_groups_params', {}).get(options['fold_group'], {})
            if pp_fold_groups_params.get('scale_target_min') and pp_fold_groups_params.get('scale_target_max'):
                corr_min = pp_fold_groups_params['scale_target_min']
                corr_max = pp_fold_groups_params['scale_target_max']

                if estimator:
                    y_pred = estimator.predict(X_test)

                y_test = y_test * corr_max + corr_min
                if isinstance(y_pred, list):
                    y_pred = np.array(y_pred)

                y_pred = y_pred * corr_max + corr_min
            else:
                logging.error("calculate_scores: no scaling found for target fold group: %s"%options['fold_group'])

        if options.get("score_top_count"):
            if y_pred is None:
                y_pred = estimator.predict(X_test)

            y_pred, y_test = sort_arrays(y_pred, y_test, options.get("score_top_count"))
            
        all_scores = {}
        if y_pred is not None:
            if options.get('binaryClassification'):
                res = confusion_matrix(y_test, y_pred).ravel()    
                #tn, fp, fn, tp
                all_scores['TN'] = 0
                all_scores['FP'] = 0
                all_scores['FN'] = 0
                all_scores['TP'] = 0

                if len(res) > 0:
                    all_scores['TN'] = res[0]
                if len(res) > 1:
                    all_scores['FP'] = res[1]
                if len(res) > 2:
                    all_scores['FN'] = res[2]
                if len(res) > 3:
                    all_scores['TP'] = res[3]
            elif options.get("task_type") == "regression":
                all_scores['mae_over'], all_scores['mae_under'] = \
                    mae_ex(y_test, y_pred)

        for scoring in options.get('scoreNames', []):
            if scoring.upper() in ['TN', 'FP', 'FN', 'TP']:
                continue

            try:
                if options.get('task_type') == "timeseries":
                    # from auger_ml.preprocessors.space import ppspace_is_timeseries_model

                    # if ppspace_is_timeseries_model(options.get('algorithm_name')) and \
                    #     scoring != options.get('scoring'):
                    #     continue
                    if scoring != options.get('scoring'):
                        continue

                if scoring == 'r2_score':
                    scoring = 'r2'

                scorer = get_scorer(scoring)
                if options.get('minority_target_class_pos') is not None:
                    argSpec = inspect.getfullargspec(scorer._score_func)
                    if 'pos_label' in argSpec.args:
                        scorer._kwargs['pos_label'] = options.get('minority_target_class_pos')
                        #logging.info("Use minority class to calculate score: %s"%scorer._kwargs)

                if y_pred is not None:
                    all_scores[scoring] = scorer._sign * scorer._score_func(y_test, y_pred, **scorer._kwargs)
                else:
                    all_scores[scoring] = _score(estimator, X_test, y_test, scorer)
                    #all_scores['scoring'] = scorer(estimator, X_test, y_test)


                if not isinstance(all_scores[scoring], list) and np.isnan(all_scores[scoring]):
                    all_scores[scoring] = 0

            except Exception as e:
                # import traceback
                # print("Score %s for algorithm %s failed to build: %s" % (
                #     scoring, options.get('algorithm_name'), str(e)))
                # print(traceback.format_exc())

                if scoring == options.get('scoring', None) and raise_main_score:
                    raise

                logging.error("Score %s for algorithm %s failed to build: %s" % (
                    scoring, options.get('algorithm_name'), str(e)))
                all_scores[scoring] = 0

        return all_scores

    @staticmethod
    def preprocess_target(model_path, data_path=None, records=None, features=None):
        ds = DataFrame.create_dataframe(data_path, records, features)

        return ModelHelper.preprocess_target_ds(model_path, ds)

    @staticmethod
    def preprocess_target_ds(model_path, ds):
        options = fsclient.read_json_file(os.path.join(model_path, "options.json"))
        target_categoricals = fsclient.read_json_file(os.path.join(model_path, "target_categoricals.json"))
        y_true =  None

        if not options.get('targetFeature') or not options.get('targetFeature') in ds.columns:
            return y_true, target_categoricals

        if options.get('timeSeriesFeatures'):
            y_true = np.ravel(ds.df[options.get('targetFeature')].astype(np.float64, copy=False), order='C')
        else:
            if target_categoricals and target_categoricals.get(options.get('targetFeature'), {}).get('categories'):
                ds.convertToCategorical(options.get('targetFeature'), is_target=True,
                    categories=target_categoricals.get(options.get('targetFeature')).get('categories'))

            y_true = np.ravel(ds.df[options.get('targetFeature')], order='C')

        return y_true, target_categoricals

    @staticmethod
    def process_prediction(ds, results, results_proba, proba_classes,
        threshold, minority_target_class, targetFeature, target_categories):

        if results_proba is not None:
            proba_classes_orig = None
            if target_categories:
                proba_classes_orig = ModelHelper.revertCategories(proba_classes, target_categories)

            results = ModelHelper.calculate_proba_target(
                results_proba, proba_classes, proba_classes_orig,
                threshold, minority_target_class)

            if proba_classes_orig is not None:
                proba_classes = proba_classes_orig

        try:
            results = list(results)
        except Exception as e:
            results = [results]

        if target_categories and results_proba is not None:
            results = ModelHelper.revertCategories(results, target_categories)

        # drop target
        if targetFeature in ds.columns:
            ds.drop([targetFeature])

        try:
            results = list(results)
        except Exception as e:
            results = [results]

        ds.df[targetFeature] = results
        if results_proba is not None:
            for idx, name in enumerate(proba_classes):
                ds.df['proba_'+str(name)] = list(results_proba[:, idx])

    @staticmethod
    def save_prediction(ds, prediction_id,
        json_result, count_in_result, prediction_date, model_path, model_id, output=None,
        gzip_predict_file=False, model_features=None):
        path_to_predict = ds.options.get('data_path')
        # Id for whole prediction (can contains many rows)
        if not prediction_id:
            prediction_id = get_uid()

        result = {}
        if path_to_predict and not json_result:
            if output:
                predict_path = output
            else:
                parent_path = os.path.dirname(path_to_predict)
                file_name = os.path.basename(path_to_predict)
                predict_path = os.path.join(parent_path, "predictions",
                    os.path.splitext(file_name)[0] + "_%s_%s_predicted.csv" % (prediction_id, model_id))

            compression = None
            if gzip_predict_file:
                predict_path += ".gz"
                compression = 'gzip'

            ds.saveToCsvFile(predict_path, compression=compression)

            if count_in_result:
                result = {'result_path': predict_path, 'count': ds.count()}
            else:
                result = predict_path
        else:
            if ds.loaded_columns or json_result:
                predicted = ds.df.to_dict('split')
                result = {'data': predicted.get('data', []), 'columns': predicted.get('columns')}
            elif ds.from_pandas:
                result = ds.df
            else:
                result = ds.df.to_dict('records')

        return result

    @staticmethod
    def revertCategories(results, categories):
        return list(map(lambda x: categories[int(x)], results))

    @staticmethod
    def calculate_proba_target(results_proba, proba_classes, proba_classes_orig,
                               threshold, minority_target_class=None):
        results = []

        if type(threshold) == str:
            try:
                threshold = float(threshold)
            except:
                try:
                    threshold = json.loads(threshold)
                except Exception as e:
                    raise Exception("Threshold '%s' should be float or hash with target classes. Error: %s" % (
                        threshold, str(e)))

        if not proba_classes_orig:
            proba_classes_orig = proba_classes

        if type(threshold) != dict:
            if minority_target_class is None:
                minority_target_class = proba_classes_orig[-1]

            threshold = {minority_target_class: threshold}

        mapped_threshold = {}

        for name, value in threshold.items():
            idx_class = None
            for idx, item in enumerate(proba_classes_orig):
                if item == name:
                    idx_class = idx
                    break

            if idx_class is None:
                raise Exception("Unknown target class in threshold: %s, %s" % (
                    name, proba_classes_orig))

            mapped_threshold[idx_class] = value

        for item in results_proba:
            proba_idx = None
            for idx, value in mapped_threshold.items():
                if item[idx] >= value:
                    proba_idx = idx
                    break

            # Find class with value > threshold from the last
            if proba_idx is None and len(mapped_threshold) == 1:
                threshold_value = list(mapped_threshold.values())[0]
                for idx, value in enumerate(item):
                    if item[len(item)-idx-1] >= threshold_value:
                        proba_idx = len(item)-idx-1
                        break

            # Find any class not minority_target_class  from the last
            if proba_idx is None:
                proba_idx = len(item)-1
                for idx, value in enumerate(item):
                    if len(item)-idx-1 not in mapped_threshold:
                        proba_idx = len(item)-idx-1
                        break

            results.append(proba_classes[proba_idx])

        return results

    @staticmethod
    def get_train_features(options):
        selected_cols = []
        for item in options.get('originalFeatureColumns', []):
            selected_cols.append(str(item))

        if options.get('targetFeature') is not None:
            selected_cols.append(options.get('targetFeature'))
        if options.get('timeSeriesFeatures'):
            selected_cols.extend(options.get('timeSeriesFeatures'))

        selected_cols.extend(ModelHelper.get_roi_features(options))
        return remove_dups_from_list(selected_cols)

    @staticmethod
    def get_roi_features(options):
        if not options.get('roi_metric'):
            return []

        roi_features = RoiCalculator(
            filter = options['roi_metric'].get('filter'),
            revenue = options['roi_metric'].get('revenue'),
            investment = options['roi_metric'].get('investment')
        ).get_var_names()
        logging.info("ROI features from roi metric: %s"%roi_features)

        return roi_features

    @staticmethod
    def create_model_options_file(options_path, scoring, target_column, task_type, binary_classification):
        options = {}
        options["targetFeature"] = target_column
        options["task_type"] = task_type
        options["scoring"] = scoring
        options["score_name"] = scoring

        if task_type == "classification":
            options["classification"] = True

        options['binaryClassification'] = True if binary_classification else False
        options['external_model'] = True

        options["scoreNames"] = ModelHelper.get_available_scores(options)

        fsclient.write_json_file(options_path, options)

        return options

    @staticmethod    
    def get_available_scores(options):
        ADD_SCORES = ['f1', 'precision', 'recall']
        SUFFIXES = ['_micro', '_macro', '_weighted']  # '_samples'

        if options.get('classification', True):
            add_scores = []
            for item in ADD_SCORES:
                add_scores.extend([item + s for s in SUFFIXES])

            if options.get('binaryClassification', False):
                advanced_binary = ['cohen_kappa_score', 'matthews_corrcoef']    # 'fowlkes_mallows_score'
                return ['accuracy', 'average_precision', 'neg_log_loss', 'roc_auc', 'gini'] \
                    + ADD_SCORES + add_scores + advanced_binary
            else:
                # jaccard_similarity_score
                return ['accuracy', 'neg_log_loss'] + add_scores
        else:
            return ['explained_variance', 'neg_median_absolute_error', 'neg_mean_absolute_error',
                    'neg_mean_squared_error', 'neg_mean_squared_log_error', 'r2', 'neg_rmsle',
                    'neg_mase', 'neg_mape', 'mda', 'neg_rmse']

    def update_model_options_file(options_path, options, ds_actuals):
        ds_actuals.options = options

        feature_columns = ds_actuals.columns
        if "targetFeature" in feature_columns:
            feature_columns.remove(options["targetFeature"])
        ds_actuals.options["featureColumns"] = feature_columns
        ds_actuals.options["originalFeatureColumns"] = feature_columns

        summary = ds_actuals.getSummary()
        binaryClassification = ds_actuals.options.get('binaryClassification', False)
        options = ds_actuals.update_options_by_dataset_statistics(summary["stat_data"])
        options['binaryClassification'] = binaryClassification
        fsclient.write_json_file(options_path, options)

        return options
