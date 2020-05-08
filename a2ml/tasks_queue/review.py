import datetime
import os

from a2ml.api.utils import dict_dig
from a2ml.tasks_queue.data_source_api_pandas import DataSourceAPIPandas
from a2ml.tasks_queue.utils import get_uid4
from a2ml.tasks_queue.config import Config
from a2ml.tasks_queue.log import logger

config = Config()

def get_model_path(provider, model_id):
    return os.path.join(config.review_data_path, provider, 'models', model_id)

# result = {'auger': {'result': True, 'data': {'predicted': '/Users/alex/data-sets/iris_predict_predicted.csv'}}}
def store_predictions(result, model_id):
    for provider in result.keys():
        if result[provider]['result']:
            data_path = dict_dig(result, provider, 'data', 'predicted')

            if data_path:
                result[provider]['data']['predicted'] = store_predictions_for_review(
                    data_path,
                    get_model_path(provider, model_id),
                )

    return result


def store_predictions_for_review(data_path, model_path, prediction_group_id=None):
    ds = DataSourceAPIPandas({'data_path': data_path})
    ds.load()

    if not 'prediction_id' in ds.columns:
        prediction_ids = []
        for i in range(0, ds.count()):
            prediction_ids.append(get_uid4())

        ds.df.insert(loc=0, column='prediction_id', value=prediction_ids)

    prediction_group_id = prediction_group_id or get_uid4()
    file_name = str(datetime.date.today()) + '_' + prediction_group_id + "_results.pkl.gz"
    res_path = os.path.join(model_path, "predictions", file_name)
    ds.saveToBinFile(res_path)
    logger.info(f'Prediction review data saved to {res_path}')

    return data_path
