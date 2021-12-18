from a2ml.api.base_a2ml import BaseA2ML
from a2ml.api.utils.show_result import show_result
#from a2ml.api.utils import convert_source
from a2ml.api.utils.context import Context


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
    def import_data(self, source=None, name=None, description=None):
        """Imports data defined in context. Uploading the same file name will result in versions being appended to the file name.

        Note:
            Your context points to a config file where ``source`` is defined.

            .. code-block:: yaml

                # Local file name, remote url to the data source file or postgres url
                source: './dataset.csv'

            .. code-block:: yaml

                # Postgres url parameters: dbname, tablename, offset(OPTIONAL), limit(OPTIONAL)
                source: jdbc:postgresql://user:pwd@ec2-54-204-21-226.compute-1.amazonaws.com:5432/dbname?tablename=table1&offset=0&limit=100

        Args:
            source (str, optional): Local file name, remote url to the data source file, Pandas DataFrame or postgres url
            name (str, optional): Name of dataset, if none then file name used. If source is DataFrame then name should be specified.
            description (str, optionsl): Description of dataset

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
        return self.runner.execute('import_data', source=source, name=name, description=description)

    @show_result
    def preprocess_data(self, data, preprocessors, locally=False):
        """Preprocess data

        Args:
            data (str|pandas.DataFrame): Input data for preprocess. Can be path to file(local or s3) or Pandas Dataframe
            preprocessors (array of dicts): List of preprocessors with parameters ::

                [
                    {'text': {'text_cols': []}}
                ]

        Preprocessors:
            text
                * text_cols(array): List of text columns to process
                * text_metrics ['mean_length', 'unique_count', 'separation_score'] : Calculate metrics for text fields and after vectorize(separation_score) 
                * tokenize (dict): Default - {'max_text_len': 30000, 'tokenizers': ['sent'], 'remove_chars': '○•'}
                * vectorize ('en_use_lg'|'hashing'|'en_use_md'|'en_use_cmlm_md'|'en_use_cmlm_lg'): See see https://github.com/MartinoMensio/spacy-universal-sentence-encoder
                * dim_reduction(dict): Generate features based on vectors. See https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html ::

                    {
                        'alg_name': 'PCA'|'t-SNE', 
                        'args': {'n_components': 2} #Number of components to keep.
                    }

                * output_prefix (str): Prefix for generated columns. Format name: {prefix}_{colname}_{num}

                * calc_distance ['none', 'cosine', 'cityblock', 'euclidean', 'haversine', 'l1', 'l2', 'manhattan', 'nan_euclidean'] | 'cosine' : See https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.distance_metrics.html#sklearn.metrics.pairwise.distance_metrics
                * compare_pairs (array of dicts): When calc_distance is not none. ::

                    [
                        {'compare_cols': [{'dataset_idx': 0, 'cols': ['col1']}, {'dataset_idx': 1, 'cols': ['col2']}], 
                            'output_name':'cosine_col1_col2', 'params': {}
                        },
                        {'compare_cols': [{'dataset_idx': 0, 'cols': ['col3']}, {'dataset_idx': 1, 'cols': ['col4']}], 
                            'output_name':'cosine_col3_col4', 'params': {}
                        },                        
                    ]

                * datasets: List of datasets to process, may be empty, so all fields takes from main dataset ::

                    [
                        {'path': 'path', 'keys': ['main_key', 'local_key'], 'text_metrics': ['separation_score', 'mean_length', 'unique_count']}, 
                        {'path': 'path1', 'keys': ['main_key1', 'local_key1']}
                    ]

        Returns:
                {
                    'result': True,
                    'data': 'data in input format'
                }

        """
        return self.get_runner(locally).execute_one_provider('preprocess_data', data, preprocessors, locally)

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
    def deploy(self, model_id, locally=False, review=True, provider=None,
            name=None, algorithm=None, score=None, data_path=None, metadata=None):
        """Deploy a model locally or to specified provider(s).

        Note:
            See evaluate function to get model_id \n
            This method support only one provider

        Args:
            model_id (str): The model id from any experiment you will deploy. Ignored for 'external' provider
            locally(bool): Deploys the model locally if True, on the Provider Cloud if False. The default is False.
            review(bool): Should model support review based on actual data. The default is True.
            provider (str): The automl provider you wish to run. For example 'auger'. The default is None - use provider defined by model_id or set in costructor.
            name (str): Friendly name for the model. Used as name for Review Endpoint
            algorithm (str): Monitored model(external provider) algorithm name.
            score (float): Monitored model(external provider) score.
            data_path (str): Data path to fit model when deploy. Return new deployed model-id
            metadata (dict): Additional parameter for the model. Used for accurcay report(report parameter)

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
                a2ml.deploy(model_id='A017AC8EAD094FD', name='FirstExperiment')

            .. code-block:: python

                ctx = Context()
                a2ml = A2ML(ctx, 'external')
                result = a2ml.deploy(model_id=None, name="My external model.", algorithm='RandomForest', score=0.75)
                model_id = result['data']['model_id']

        """
        return self.get_runner(locally, model_id, provider).execute_one_provider('deploy',
            model_id, locally, review, name, algorithm, score, data_path, metadata)

    @show_result
    def predict(self, model_id, filename=None, data=None, columns=None, predicted_at=None,
            threshold=None, score=False, score_true_data=None,
            output=None, no_features_in_result = None, locally=False, provider=None):
        """Predict results with new data against deployed model. Predictions are stored next to the file with data to be predicted on. The file name will be appended with suffix _predicted.

        Note:
            Use deployed model_id \n
            This method support only one provider

        Args:
            model_id(str): The deployed model id you want to use.
            filename(str): The file with data to request predictions for.
            data: array of records [[target, actual]] or Pandas DataFrame (target, actual) or dict created with Pandas DataFrame to_dict('list') method
            columns(list): list of column names if data is array of records
            predicted_at: Predict data date. Use for review of historical data.
            threshold(float): For classification models only. This will return class probabilities with response.
            score(bool): Calculate scores for predicted results.
            score_true_data(str, pandas.DataFrame, dict): Data with true values to calculate scores. If missed, target from filename used for true values.
            output(str): Output csv file path.
            no_features_in_result(bool) : Do not return feature columns in prediction result. False by default
            locally(bool, str): Predicts using a local model with auger.ai.predict if True, on the Provider Cloud if False. If set to "docker", then docker image used to run the model
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
                    'data': {'predicted': [{col1: value1, col2: value2, target: predicted_value1}, {col1: value3, col2: value4, target: predicted_value2}]}
                }

            if filename is None and data is not None and columns is not None. ::

                {
                    'result': True,
                    'data': {'predicted': {'columns': ['col1', 'col2', target], 'data': [['value1', 'value2', 1], ['value3', 'value4', 0]]}}
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                rv = A2ML(ctx).predict(model_id, '../irises.csv')
                # if rv[provider].result is True
                # predictions are stored in rv[provider]['data']['predicted']

            .. code-block:: python

                ctx = Context()
                data = [{'col1': 'value1', 'col2': 'value2'}, {'col1': 'value3', 'col2': 'value4'}]
                rv = A2ML(ctx).predict(model_id, data=data)
                # if rv[provider].result is True
                # predictions are returned as rv[provider]['data']['predicted']

            .. code-block:: python

                ctx = Context()
                data = [['value1', 'value2'], ['value3', 'value4']]
                columns = ['col1', 'col2']
                rv = A2ML(ctx).predict(model_id, data=data)
                # if rv[provider].result is True
                # predictions are returned as rv[provider]['data']['predicted']

            .. code-block:: python
                
                # Predict locally without config files. Model will automatically downloaded if not exists.
                # To use local predict install a2ml[predict]
                ctx = Context()
                ctx.config.set('name', 'project name')
                ctx.credentials = "Json string from a2ml ui settings"

                rv = A2ML(ctx).predict(model_id, '../irises.csv',
                    no_features_in_result = True, locally=True)
                # if rv[provider].result is True
                # predictions are stored in rv[provider]['data']['predicted']

        """
        return self.get_runner(locally, model_id, provider).execute_one_provider('predict', filename, model_id, 
            threshold, locally, data, columns, predicted_at, output, no_features_in_result,
            score, score_true_data )

    @show_result
    def actuals(self, model_id, filename=None, data=None, columns=None, actuals_at=None, 
            actual_date_column=None, experiment_params=None, locally=False, provider=None):
        """Submits actual results(ground truths) for predictions of a deployed model. This is used to review and monitor active models.

        Note:
            It is assumed you have predictions against this model first.

            .. list-table:: actuals.csv
                :widths: 50 50 50
                :header-rows: 1

                * - predicted( or target): predicted value. If missed - predict called automatically
                  - actual
                  - baseline_target: predicted value for baseline model (OPTIONAL)
                * - Iris-setosa
                  - Iris-setosa
                  - Iris-setosa
                * - Iris-virginica
                  - Iris-virginica
                  - Iris-virginica

            It may also contain train features to predict(if target missed), retrain model while Review and for distribution chart

            This method support only one provider

        Args:
            model_id(str): The deployed model id you want to use.
            filename(str): The file with data to request predictions for.
            data: array of records [[target, actual]] or Pandas DataFrame (target, actual) or dict created with Pandas DataFrame to_dict('list') method
            columns(list): list of column names if data is array of records
            actuals_at: Actuals date. Use for review of historical data.
            actual_date_column(str): name of column in data which contains actual date
            experiment_params(dict): parameters to calculate experiment metrics ::

                start_date(date): experiment actuals start date
                end_date(date):  experiment actuals end date
                date_col(str): column name with date

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
                A2ML(ctx).actuals('D881079E1ED14FB', filename=<path_to_file>/actuals.csv)

            .. code-block:: python

                ctx = Context()
                actual_records = [['predicted_value_1', 'actual_value_1'], ['predicted_value_2', 'actual_value_2']]
                columns = [target, 'actual']

                A2ML(ctx).actuals('D881079E1ED14FB', data=actual_records,columns=columns)

            .. code-block:: python

                ctx = Context()
                actual_records = [['predicted_value_1', 'actual_value_1'], ['predicted_value_2', 'actual_value_2']]
                columns = [target, 'actual']

                A2ML(ctx, "external").actuals('external_model_id', data=actual_records,columns=columns)

        """
        return self.get_runner(locally, model_id, provider).execute_one_provider('actuals', 
            model_id, filename, data, columns, actuals_at, actual_date_column, experiment_params, locally)


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
        """Review information about deployed model.

        Args:
            model_id(str): The deployed model id you want to use.
            locally(bool): Process review locally.

        Returns:
            status(str): May be : started, error, completed, retrain
            error(str): Description of error if status='error'
            accuracy(float): Average accuracy of model(based on used metric) for review sensitivity period(see config.yml)

            ::

                {
                    'result': True,
                    'data': {'status': 'completed', 'error': '', 'accuracy': 0.76}
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                result = A2ML(ctx).review(model_id='D881079E1ED14FB')
        """
        return self.get_runner(locally, model_id, provider).execute_one_provider('review', model_id)
