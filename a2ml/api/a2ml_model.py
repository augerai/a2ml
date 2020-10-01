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
    def deploy(self, model_id, locally=False, review=True, provider=None):
        """Deploy a model locally or to specified provider(s).

        Args:
            model_id (str): Model ID from the any experiment leaderboard.
            locally(bool): Deploys using a local model if True, on the Provider Cloud if False.
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
                model = A2MLModel(ctx).deploy(model_id='D881079E1ED14FB', locally=True)
        """
        return self.get_runner(locally, model_id, provider).execute_one_provider('deploy', model_id, locally, review)

    @show_result
    def predict(self, filename,
      model_id, threshold=None, locally=False, data=None, columns=None, predicted_at=None, output=None, provider=None):
        """Predict results with new data against deployed model. Predictions are stored next to the file with data to be predicted on. The file name will be appended with suffix _predicted.

        Note:
            Use deployed model_id \n
            This method support only one provider
            If you pass prediction_id column in input data, it will be return in predict result. Otherwise unique prediction_id will be generated for each record.

        Args:
            filename(str): The file with data to request predictions for.
            model_id(str): The deployed model id you want to use.
            threshold(float): For classification models only. This will return class probabilities with response.
            locally(bool): Predicts using a local model if True, on the Provider Cloud if False.
            data: dict or array of records or Pandas DataFrame
            columns(list): list of column names if data is array of records
            predicted_at: Predict data date. Use for review of historical data.
            output(str): Output csv file path.
            provider (str): The automl provider you wish to run. For example 'auger'. The default is None - use provider defined by model_id or set in costructor.

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
                rv = A2MLModel(ctx).predict('../irises.csv', model_id)
                # if rv[provider].result is True
                # predictions are stored in rv[provider]['data']['predicted']

            .. code-block:: python

                ctx = Context()
                data = [{'col1': 'value1', 'col2': 'value2'}, {'col1': 'value3', 'col2': 'value4'}]
                rv = A2MLModel(ctx).predict(None, model_id, data=data)
                # if rv[provider].result is True
                # predictions are returned as rv[provider]['data']['predicted']

            .. code-block:: python

                ctx = Context()
                data = [['value1', 'value2'], ['value3', 'value4']]
                columns = ['col1', 'col2']                
                rv = A2MLModel(ctx).predict(None, model_id, data=data)
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

        Args:
            model_id(str): The deployed model id you want to use.
            filename(str): The file with data to request predictions for.
            actual_records: array of records [[prediction_id, actual]] or Pandas DataFrame (prediction_id, actual)
            actuals_at: Actuals date. Use for review of historical data.
            locally(bool): Process actuals locally.
            provider (str): The automl provider you wish to run. For example 'auger'. The default is None - use provider defined by model_id or set in costructor.

        Returns:
            ::

                {
                    'result': True,
                    'data': True
                }

            Errors. ::

                {
                    'auger': {
                        'result': False,
                        'data': 'Actual Prediction IDs not found in model predictions.'
                    }
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                model = A2MLModel(ctx).actuals('D881079E1ED14FB', filename=<path_to_file>/actuals.csv)

            .. code-block:: python
            
                # To pass just one actual:
                ctx = Context()
                actual_records = [['prediction_id', 'actual_value']]
                model = A2MLModel(ctx).actuals('D881079E1ED14FB', actual_records=actual_records)

            .. code-block:: python

                ctx = Context()
                actual_records = [['prediction_1', 'value1'], ['prediction_2', 'value2']]
                model = A2MLModel(ctx).actuals('D881079E1ED14FB', actual_records=actual_records)

        """
        return self.get_runner(locally, model_id, provider).execute_one_provider('actuals', model_id, filename, actual_records, actuals_at, locally)

    @show_result
    def review_alert(self, model_id, parameters = None, locally=False, provider=None):
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
                * action (no/retrain/retrain_deploy)

                    - no: no action should be executed
                    - retrain: Use new predictions and actuals as test set to retrain the model.
                    - retrain_deploy: Deploy retrained model and make it active model of this endpoint.

                * notification (no/user/organization): Send message via selected notification channel.

            locally(bool): Process review locally.
            provider (str): The automl provider you wish to run. For example 'auger'. The default is None - use provider defined by model_id or set in costructor.

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
        return self.get_runner(locally, model_id, provider).execute_one_provider('review_alert', model_id, parameters)

    @show_result
    def review(self, model_id, locally=False, provider=None):
        """Review information about deployed model.

        Args:
            model_id(str): The deployed model id you want to use.
            locally(bool): Process review locally.
            provider (str): The automl provider you wish to run. For example 'auger'. The default is None - use provider defined by model_id or set in costructor.

        Returns:
            ::

                {
                    'result': True,
                    'data': {'status': 'completed', 'error': ''}
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                model = A2MLModel(ctx).review(model_id='D881079E1ED14FB')
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
