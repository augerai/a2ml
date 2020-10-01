import datetime
import os
import logging
import numpy as np
import json

from a2ml.api.utils import get_uid, get_uid4, fsclient, remove_dups_from_list
from a2ml.api.utils.dataframe import DataFrame


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
    def get_project_path():
        root_dir, root_tmp_dir = ModelHelper.get_root_paths()
        return os.path.join(root_dir, os.environ.get('AUGER_PROJECT_PATH', ''))

    @staticmethod
    def get_models_path(project_path=None):
        if not project_path:
            project_path = ModelHelper.get_project_path()
        return os.path.join(project_path, "models")

    @staticmethod
    def get_model_path(model_id, project_path=None):
        if model_id:
            return os.path.join(ModelHelper.get_models_path(project_path), model_id)

    @staticmethod
    def get_metrics_path(params):
        project_path = params.get('hub_info', {}).get('project_path')
        if not project_path:
            project_path = ModelHelper.get_project_path()

        if params.get('hub_info', {}).get('experiment_id') and params.get('hub_info', {}).get('experiment_session_id'):
            return os.path.join(project_path, "channels", params['hub_info']['experiment_id'],
                "project_runs", params['hub_info']['experiment_session_id'], "metrics")

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
    #     from sklearn.metrics.scorer import get_scorer
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
        from sklearn.metrics.scorer import get_scorer
        from sklearn.model_selection._validation import _score
        # For calculate_scores
        from .scores.regression import spearman_correlation_score
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

        all_scores = {}
        for scoring in options.get('scoreNames', []):
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


                if np.isnan(all_scores[scoring]):
                    all_scores[scoring] = 0

            except Exception as e:
                #logging.exception("Score failed.")
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
    def save_prediction(ds, prediction_id, support_review_model,
        json_result, count_in_result, prediction_date, model_path, model_id, output=None, gzip_predict_file=False,
        prediction_id_col=None,model_features=None):
        if prediction_id_col is not None:
            ds.df['prediction_id'] = prediction_id_col
        else:
            # Ids for each row of prediction (prediction row's ids)
            prediction_ids = []
            for i in range(0, ds.count()):
                prediction_ids.append(get_uid4())

            ds.df.insert(loc=0, column='prediction_id', value=prediction_ids)

        return ModelHelper.save_prediction_result(ds, prediction_id, support_review_model,
            json_result, count_in_result, prediction_date, model_path, model_id, output, 
            gzip_predict_file=gzip_predict_file, model_features=model_features)

    @staticmethod
    def save_prediction_result(ds, prediction_id, support_review_model,
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

        if support_review_model:
            file_name = str(prediction_date or datetime.date.today()) + \
                '_' + prediction_id + "_results.feather.zstd"
            #Save only model features, they should contain target and prediction_id    
            if model_features:
                ds.select(model_features)

            ds.saveToFeatherFile(os.path.join(
                model_path, "predictions", file_name))

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

        return remove_dups_from_list(selected_cols)

