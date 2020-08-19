from a2ml.api.base_a2ml import BaseA2ML
from a2ml.api.utils.show_result import show_result
from a2ml.api.utils import convert_source


class A2ML(BaseA2ML):
    """Facade to A2ML providers."""

    def __init__(self, ctx, provider = None):
        """Initializes A2ML PREDIT instance.

        Args:
            ctx (object): An instance of the a2ml Context.
            provider (str): The automl provider(s) you wish to run. For example 'auger,azure,google'. The default is None - use provider set in config.

        Returns:
            A2ML object

        Examples:
            .. code-block:: python

                ctx = Context()
                a2ml = A2ML(ctx, 'auger, azure')
        """
        super(A2ML, self).__init__(ctx, None)
        self.runner = self.build_runner(ctx, provider)
        self.local_runner = lambda: self.build_runner(ctx, provider, force_local=True)

    @show_result
    def import_data(self, source=None):
        """Imports data defined in context. Uploading the same file name will result in versions being appended to the file name.

        Note:
            Your context points to a config file where ``source`` is defined.

            .. code-block:: yaml

                # Local file name or remote url to the data source file
                source: './dataset.csv'

        Args:
            source (str, optional): Local file name or remote url to the data source file or Pandas DataFrame

        Returns:
            Results for each provider. ::

                {
                    'auger': {'result': True, 'data': {'created': 'dataset.csv'}}, \n
                    'azure': {'result': True, 'data': {'created': 'dataset.csv'}}
                }

            Errors. ::

                {
                    'auger': {'result': False, 'data': 'Please specify data source file...'}, \n
                    'azure': {'result': False, 'data': 'Please specify data source file...'}
                }


        Examples:
            .. code-block:: python

                ctx = Context()
                a2ml = A2ML(ctx, 'auger, azure')
                a2ml.import_data()
        """
        with convert_source(source, self.ctx.config.get("name", "source_data")) as data_source:
            return self.runner.execute('import_data', source=data_source)

    @show_result
    def train(self):
        """Starts training session based on context state.

        Returns:
            Results for each provider. ::

                {
                    'auger': {
                        'result': True,
                        'data': {
                            'experiment_name': 'dataset.csv-4-experiment',
                            'session_id': '9ccfe04eca67757a'
                         }
                    },
                    'azure': {
                        'result': True,
                        'data': {
                            'experiment_name': 'dataset.csv-4-experiment',
                            'session_id': '9ccfe04eca67757a'
                         }
                    }
                }

            Errors. ::

                {
                    'auger': {'result': False, 'data': 'Please set target to build model.'}, \n
                    'azure': {'result': False, 'data': 'Please set target to build model.'}
                }

        Examples:

            .. code-block:: python

                ctx = Context()
                a2ml = A2ML(ctx, 'auger, azure')
                a2ml.train()

        """
        return self.runner.execute('train')

    @show_result
    def evaluate(self, run_id = None):
        """Evaluate the results of training.

        Args:
            run_id (str, optional): The run id for a training session. A unique run id is created for every train. Default is last experiment train.
        
        Returns:
            Results for each provider. ::

                {
                    'auger': {
                        'result': True,
                        'data': {
                            'run_id': '9ccfe04eca67757a',
                            'leaderboard': [
                                {'model id': 'A017AC8EAD094FD', 'rmse': '0.0000', 'algorithm': 'LGBMRegressor'},
                                {'model id': '4602AFCEEEAE413', 'rmse': '0.0000', 'algorithm': 'ExtraTreesRegressor'}
                            ],
                            'trials_count': 10,
                            'status': 'started',
                            'provider_status': 'provider specific'
                        }
                    },
                    'azure': {
                        'result': True,
                        'data': {
                            'run_id': '9ccfe04eca67757a',
                            'leaderboard': [
                                {'model id': 'A017AC8EAD094FD', 'rmse': '0.0000', 'algorithm': 'LGBMRegressor'},
                                {'model id': '4602AFCEEEAE413', 'rmse': '0.0000', 'algorithm': 'ExtraTreesRegressor'}
                            ],
                            'trials_count': 10,
                            'status': 'started',
                            'provider_status': 'provider specific'                            
                        }
                    }                    
                }

            **Status**

                * **preprocess** - search is preprocessing data for traing
                * **started** - search is in progress
                * **completed** - search is completed
                * **interrupted** - search was interrupted
                * **error** - search was finished with error

        Examples:
            .. code-block:: python

                ctx = Context()
                a2ml = A2ML(ctx, 'auger, azure')
                while True:
                    res = a2ml.evaluate()
                    if status['auger']['status'] not in ['preprocess','started']:
                        break
        """
        return self.runner.execute('evaluate', run_id = run_id)

    @show_result
    def deploy(self, model_id, locally=False, review=True, provider=None):
        """Deploy a model locally or to specified provider(s).

        Note:
            See evaluate function to get model_id \n
            This method support only one provider

        Args:
            model_id (str): The model id from any experiment you will deploy.
            locally(bool): Deploys the model locally if True, on the Provider Cloud if False. The default is False.
            review(bool): Should model support review based on actual data. The default is True.
            provider (str): The automl provider you wish to run. For example 'auger'. The default is None - use provider defined by model_id or set in costructor.

        Returns:
            ::

                {
                    'result': True,
                    'data': {'model_id': 'A017AC8EAD094FD'}
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                a2ml = A2ML(ctx, 'auger, azure')
                a2ml.deploy(model_id='A017AC8EAD094FD')
        """
        return self.get_runner(locally, model_id, provider).execute_one_provider('deploy', model_id, locally, review)

    @show_result
    def predict(self, filename,
      model_id, threshold=None, locally=False, data=None, columns=None, predicted_at=None, output=None, provider=None):
        """Predict results with new data against deployed model. Predictions are stored next to the file with data to be predicted on. The file name will be appended with suffix _predicted.

        Note:
            Use deployed model_id \n
            This method support only one provider

        Args:
            filename(str): The file with data to request predictions for.
            model_id(str): The deployed model id you want to use.
            threshold(float): For classification models only. This will return class probabilities with response.
            locally(bool): Predicts using a local model if True, on the Provider Cloud if False.
            data: dict or array of records or Pandas DataFrame
            columns(list): list of column names if data is array of records
            predicted_at: Predict data date. Use for review of historical data.
            output(str): Output csv file path.
            provider (str): The automl provider you wish to run. For example 'auger'. The default is None - use provider set in costructor or config.

        Returns:
            if filename is not None. ::

                {
                    'result': True,
                    'data': {'predicted': 'dataset_predicted.csv'}
                }

            if filename is None and data is not None and columns is None. ::

                {
                    'result': True,
                    'data': {'predicted': [{col1: value1, col2: value2}, {col1: value3, col2: value4}]}
                }

            if filename is None and data is not None and columns is not None. ::

                {
                    'result': True,
                    'data': {'predicted': {'columns': ['col1', 'col2'], 'data': [['value1', 'value2'], ['value3', 'value4']]}}
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                rv = A2ML(ctx).predict('../irises.csv', model_id)
                # if rv[provider].result is True
                # predictions are stored in rv[provider]['data']['predicted']

            .. code-block:: python

                ctx = Context()
                data = [{'col1': 'value1', 'col2': 'value2'}, {'col1': 'value3', 'col2': 'value4'}]
                rv = A2ML(ctx).predict(None, model_id, data=data)
                # if rv[provider].result is True
                # predictions are returned as rv[provider]['data']['predicted']

            .. code-block:: python

                ctx = Context()
                data = [['value1', 'value2'], ['value3', 'value4']]
                columns = ['col1', 'col2']                
                rv = A2ML(ctx).predict(None, model_id, data=data)
                # if rv[provider].result is True
                # predictions are returned as rv[provider]['data']['predicted']

        """
        return self.get_runner(locally, model_id, provider).execute_one_provider('predict', filename, model_id, threshold, locally, data, columns, predicted_at, output)

    @show_result
    def actuals(self, model_id, filename=None, actual_records=None, actuals_at=None, locally=False, provider=None):
        """Submits actual results(ground truths) for predictions of a deployed model. This is used to review and monitor active models.

        Note:
            It is assumed you have predictions against this model first. The file will need to fill in actual values for prediction_id.

            .. list-table:: actuals.csv
                :widths: 50 50
                :header-rows: 1

                * - prediction_id
                  - actual
                * - eaed9cd8-ba49-4c06-86d5-71d453c681d1
                  - Iris-setosa
                * - eaed9cd8-ba49-4c06-86d5-71d453c65290
                  - Iris-virginica

            This method support only one provider

        Args:
            model_id(str): The deployed model id you want to use.
            filename(str): The file with data to request predictions for.
            actual_records: array of records [[prediction_id, actual]] or Pandas DataFrame (prediction_id, actual)
            actuals_at: Actuals date. Use for review of historical data.
            locally(bool): Process actuals locally.
            provider (str): The automl provider you wish to run. For example 'auger'. The default is None - use provider set in costructor or config.

        Returns:
            ::

                {
                    'result': True,
                    'data': True
                }

            Errors. ::

                {
                    'result': False,
                    'data': 'Actual Prediction IDs not found in model predictions.'
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                model = A2MLModel(ctx).actuals('D881079E1ED14FB', filename=<path_to_file>/actuals.csv)

            .. code-block:: python
            
                # To pass just one actual:
                ctx = Context()
                actual_records = [['prediction_id', 'actual_value']]
                model = A2ML(ctx).actuals('D881079E1ED14FB', actual_records=actual_records)

            .. code-block:: python

                ctx = Context()
                actual_records = [['prediction_1', 'value1'], ['prediction_2', 'value2']]
                model = A2ML(ctx).actuals('D881079E1ED14FB', actual_records=actual_records)

        """
        return self.get_runner(locally, model_id, provider).execute_one_provider('actuals', model_id, filename, actual_records, actuals_at, locally)


    @show_result
    def delete_actuals(self, model_id, with_predictions=False, begin_date=None, end_date=None, locally=False, provider=None):
        """Delete files with actuals and predcitions locally or from specified provider(s).

        Args:
            model_id (str): Model ID to delete actuals and predictions.
            with_predictions(bool): 
            begin_date: Date to begin delete operations 
            end_date: Date to end delete operations 
            locally(bool): Delete files from local model if True, on the Provider Cloud if False. The default is False.
            provider (str): The automl provider you wish to run. For example 'auger'. The default is None - use provider defined by model_id or set in costructor.

        Returns:
            ::

                {
                    'result': True,
                    'data': None
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                A2MLModel(ctx).delete_actuals(model_id='D881079E1ED14FB')
        """
        return self.get_runner(locally, model_id, provider).execute_one_provider('delete_actuals', model_id, with_predictions, begin_date, end_date, locally)


    @show_result
    def review(self, model_id, locally=False, provider=None):
        """Review the performance of deployed model.

        Args:
            model_id(str): The deployed model id you want to use.
            locally(bool): Process review locally.

        Returns:
            ::

                {
                    'result': True,
                    'data': {'score': {'accuracy': 0.8}}
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                model = A2ML(ctx).review(model_id='D881079E1ED14FB')
        """
        return self.get_runner(locally, model_id, provider).execute_one_provider('review', model_id)
