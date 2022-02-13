from a2ml.api.base_a2ml import BaseA2ML
from a2ml.api.utils.show_result import show_result

class A2MLModel(BaseA2ML):
    """Contains the model operations that interact with provider."""
    def __init__(self, ctx, provider=None):
        """Initializes a new a2ml model.

        Args:
            ctx (object): An instance of the a2ml Context.
            provider (str): The automl provider you wish to run. For example 'auger'. The default is None - use provider from methods.

        Returns:
            A2MLModel object

        Examples:
            .. code-block:: python

                ctx = Context()
                model = A2MLModel(ctx)
        """
        super(A2MLModel, self).__init__(ctx, "model")

        self.runner = self.build_runner(ctx, provider)
        self.local_runner = lambda: self.build_runner(ctx, provider, force_local=True)

    @show_result
    def deploy(self, model_id, locally=False, review=False, provider=None,
        name=None, algorithm=None, score=None, data_path=None, metadata=None):
        """Deploy a model locally or to specified provider(s).

        Args:
            model_id (str): Model ID from the any experiment leaderboard.
            locally(bool): Deploys using a local model if True, on the Provider Cloud if False.
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
                model = A2MLModel(ctx).deploy(model_id='D881079E1ED14FB', name='FirstExperiment')

            .. code-block:: python

                ctx = Context()
                model = A2MLModel(ctx, 'external')
                result = model.deploy(model_id=None, name="My external model.", algorithm='RandomForest', score=0.75)
                model_id = result['data']['model_id']

        """
        return self.get_runner(locally, model_id, provider).execute_one_provider('deploy',
            model_id, locally, review, name, algorithm, score, data_path, metadata)

    @show_result
    def predict(self, model_id, filename=None, data=None, columns=None, predicted_at=None,
            threshold=None, score=False, score_true_data=None,
            output=None, no_features_in_result=None, locally=False, provider=None):
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
                rv = A2MLModel(ctx).predict(model_id, '../irises.csv')
                # if rv[provider].result is True
                # predictions are stored in rv[provider]['data']['predicted']

            .. code-block:: python

                ctx = Context()
                data = [{'col1': 'value1', 'col2': 'value2'}, {'col1': 'value3', 'col2': 'value4'}]
                rv = A2MLModel(ctx).predict(model_id, data=data)
                # if rv[provider].result is True
                # predictions are returned as rv[provider]['data']['predicted']

            .. code-block:: python

                ctx = Context()
                data = [['value1', 'value2'], ['value3', 'value4']]
                columns = ['col1', 'col2']
                rv = A2MLModel(ctx).predict(model_id, data=data)
                # if rv[provider].result is True
                # predictions are returned as rv[provider]['data']['predicted']

            .. code-block:: python
                
                # Predict locally without config files. Model will automatically downloaded if not exists.
                # To use local predict install a2ml[predict]
                ctx = Context()
                ctx.config.set('name', 'project name')
                ctx.credentials = "Json string from a2ml ui settings"

                rv = A2MLModel(ctx).predict(model_id, '../irises.csv',
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

                * - predicted ( or target): predicted value. If missed - predict called automatically
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
                A2MLModel(ctx).actuals('D881079E1ED14FB', filename=<path_to_file>/actuals.csv)

            .. code-block:: python

                ctx = Context()
                actual_records = [['predicted_value_1', 'actual_value_1'], ['predicted_value_2', 'actual_value_2']]
                columns = [target, 'actual']

                A2MLModel(ctx).actuals('D881079E1ED14FB', data=actual_records,columns=columns)

            .. code-block:: python

                ctx = Context()
                actual_records = [['predicted_value_1', 'actual_value_1'], ['predicted_value_2', 'actual_value_2']]
                columns = [target, 'actual']

                A2MLModel(ctx, "external").actuals('external_model_id', data=actual_records,columns=columns)

        """
        return self.get_runner(locally, model_id, provider).execute_one_provider('actuals', 
            model_id, filename, data, columns, actuals_at, actual_date_column, experiment_params, locally)

    @show_result
    def review_alert(self, model_id, parameters = None, locally=False, provider=None, name=None):
        """Update Review parameters.

        Args:
            model_id(str): The deployed model id you want to use.
            parameters(dict): If None, review section from config will be used.

                * active (True/False): Activate/Deactivate Review Alert
                * type (model_accuracy/feature_average_range/runtime_errors_burst)

                    - model_accuracy: Decrease in Model Accuracy: the model accuracy threshold allowed before trigger is initiated. Default threshold: 0.7. Default sensitivity: 72
                    - feature_average_range: Feature Average Out-Of-Range: Trigger an alert if average feature value during time period goes beyond the standard deviation range calculated during training period by the specified number of times or more. Default threshold: 1. Default sensitivity: 168
                    - runtime_errors_burst: Burst Of Runtime Errors: Trigger an alert if runtime error count exceeds threshold. Default threshold: 5. Default sensitivity: 1

                * threshold (float)
                * sensitivity (int): The amount of time(in hours) this metric must be at or below the threshold to trigger the alert.
                * threshold_policy (all_values/average_value/any_value)

                    - all_values: Default value. Trigger an alert when all values in sensitivity below threshold
                    - average_value: Trigger an alert when average of values in sensitivity below threshold
                    - any_value: Trigger an alert when any value in sensitivity below threshold

                * action (no/retrain/retrain_deploy)

                    - no: no action should be executed
                    - retrain: Use new predictions and actuals as test set to retrain the model.
                    - retrain_deploy: Deploy retrained model and make it active model of this endpoint.

                * notification (no/user/organization): Send message via selected notification channel.

            locally(bool): Process review locally.
            provider (str): The automl provider you wish to run. For example 'auger'. The default is None - use provider defined by model_id or set in costructor.
            name (str): Friendly name for the model. Used as name for Review Endpoint

        Returns:
            ::

                {
                    'result': True,
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                model = A2MLModel(ctx).review_alert(model_id='D881079E1ED14FB')
        """
        return self.get_runner(locally, model_id, provider).execute_one_provider('review_alert', model_id, parameters, name)

    @show_result
    def review(self, model_id, locally=False, provider=None):
        """Review information about deployed model.

        Args:
            model_id(str): The deployed model id you want to use.
            locally(bool): Process review locally.
            provider (str): The automl provider you wish to run. For example 'auger'. The default is None - use provider defined by model_id or set in costructor.

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
                result = A2MLModel(ctx).review(model_id='D881079E1ED14FB')
        """
        return self.get_runner(locally, model_id, provider).execute_one_provider('review', model_id)

    @show_result
    def undeploy(self, model_id, locally=False, provider=None):
        """Undeploy a model locally or from specified provider(s).

        Args:
            model_id (str): Model ID from any experiment leaderboard.
            locally(bool): Deploys using a local model if True, on the Provider Cloud if False. The default is False.
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
                model = A2MLModel(ctx).undeploy(model_id='D881079E1ED14FB', locally=True)
        """
        return self.get_runner(locally, model_id, provider).execute_one_provider('undeploy', model_id, locally)

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
    def get_info(self, model_id, locally=False, provider=None):
        """Get information about model

        Args:
            model_id (str): Model ID to delete actuals and predictions.
            locally(bool): Get information from local model if True, on the Provider Cloud if False. The default is False.
            provider (str): The automl provider you wish to run. For example 'auger'. The default is None - use provider defined by model_id or set in costructor.

        Returns:
            ::

                {
                    'result': True,
                    'data': {} #detailed model information
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                res = A2MLModel(ctx).get_info('D881079E1ED14FB')
        """
        return self.get_runner(locally, model_id, provider).execute_one_provider('get_info', model_id, locally)

    @show_result
    def update(self, model_id, metadata, locally=False, provider=None):
        """Update model metadata

        Args:
            model_id (str): Model ID to delete actuals and predictions.
            metadata (dict): Model metadata to update
            locally(bool): Get information from local model if True, on the Provider Cloud if False. The default is False.
            provider (str): The automl provider you wish to run. For example 'auger'. The default is None - use provider defined by model_id or set in costructor.

        Returns:
            ::

                {
                    'result': True,
                    'data': {}
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                res = A2MLModel(ctx).update('D881079E1ED14FB', {'report': {}})
        """
        return self.get_runner(locally, model_id, provider).execute_one_provider('update', model_id, metadata, locally)
