import datetime
import os

from a2ml.api.utils import get_uid, get_uid4


class ModelHelper(object):

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
            # print("INFO: Prediction result with type: %s convert to list failed: %s"%(type(results), str(e)))
            results = [results]

        if target_categories:
            results = ModelHelper.revertCategories(results, target_categories)

        # drop target
        if targetFeature in ds.columns:
            ds.drop([targetFeature])

        try:
            results = list(results)
        except Exception as e:
            # print("INFO: Prediction result with type: %s convert to list failed: %s"%(type(results), str(e)))
            results = [results]

        ds.df[targetFeature] = results
        if results_proba is not None:
            for idx, name in enumerate(proba_classes):
                ds.df['proba_'+str(name)] = list(results_proba[:, idx])

    @staticmethod
    def save_prediction(ds, prediction_id, support_review_model, 
        json_result, count_in_result, prediction_date, model_path, model_id, output=None):
        # Ids for each row of prediction (predcition row's ids)
        prediction_ids = []
        for i in range(0, ds.count()):
            prediction_ids.append(get_uid4())

        ds.df.insert(loc=0, column='prediction_id', value=prediction_ids)

        return ModelHelper.save_prediction_result(ds, prediction_id, support_review_model, 
            json_result, count_in_result, prediction_date, model_path, model_id, output)

    @staticmethod
    def save_prediction_result(ds, prediction_id, support_review_model, 
        json_result, count_in_result, prediction_date, model_path, model_id, output=None):
        path_to_predict = ds.options.get('data_path')
        # Id for whole prediction (can contains many rows)
        if not prediction_id:
            prediction_id = get_uid()

        if support_review_model:
            file_name = str(prediction_date or datetime.date.today()) + \
                '_' + prediction_id + "_results.feather.zstd"
            ds.saveToFeatherFile(os.path.join(
                model_path, "predictions", file_name))

        if path_to_predict and not json_result:
            if output:
                predict_path = output
            else:    
                parent_path = os.path.dirname(path_to_predict)
                file_name = os.path.basename(path_to_predict)
                predict_path = os.path.join(parent_path, "predictions",
                    os.path.splitext(file_name)[0] + "_%s_%s_predicted.csv" % (prediction_id, model_id))

            ds.saveToCsvFile(predict_path, compression=None)

            if count_in_result:
                return {'result_path': predict_path, 'count': ds.count()}
            else:
                return predict_path
        else:
            if json_result:
                return ds.df.to_json(orient='split', index=False)

            if ds.loaded_columns:
                predicted = ds.df.to_dict('split')
                return {'data': predicted.get('data', []), 'columns': predicted.get('columns')}

            return ds.df.to_dict('records')

    @staticmethod
    def revertCategories(results, categories):
        return list(map(lambda x: categories[int(x)], results))

    @staticmethod
    def calculate_proba_target(results_proba, proba_classes, proba_classes_orig,
                               threshold, minority_target_class=None):
        import json
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

        #print("Prediction threshold: %s, %s"%(threshold, proba_classes_orig))
        # print(results_proba)
        if type(threshold) == dict:
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

                if proba_idx is None:
                    proba_idx = 0
                    for idx, value in enumerate(item):
                        if idx not in mapped_threshold:
                            proba_idx = idx
                            break

                results.append(proba_classes[proba_idx])
        else:
            # TODO: support multiclass classification
            for item in results_proba:
                max_proba_idx = 0
                for idx, prob in enumerate(item):
                    if prob > item[max_proba_idx]:
                        max_proba_idx = idx

                if item[max_proba_idx] < threshold:
                    if max_proba_idx > 0:
                        max_proba_idx = 0
                    else:
                        max_proba_idx = 1

                results.append(proba_classes[max_proba_idx])

        return results
