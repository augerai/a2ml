from a2ml.api.base_a2ml import BaseA2ML
from a2ml.api.utils.show_result import show_result

class A2MLModel(BaseA2ML):
    """Contains the model operations that interact with provider."""
    def __init__(self, ctx, provider):
        """Initializes a new a2ml model.

        Args:
            context (object): An instance of the a2ml Context.
            provider (str): The automl provider(s) you wish to run. For example 'auger,azure,google'.
        
        Returns:
            A2MLModel object

        Examples:
            .. code-block:: python

                ctx = Context()
                model = A2MLModel(ctx, 'auger, azure')
        """
        super(A2MLModel, self).__init__()
        self.ctx = ctx
        self.provider = provider
        self.runner = self.build_runner(ctx, provider, 'model')
        self.local_runner = lambda: self.build_runner(ctx, provider, 'model', force_local=True)

    @show_result
    def deploy(self, model_id, locally):
        """Deploy a model locally or to specified provider(s).

        Args:
            model_id (str): Model ID from the any experiment leaderboard.
            locally(bool): Deploys using a local model if True, on the Provider Cloud if False.
        
        Returns:
            Results for provider. ::

                {
                    'auger': {
                        'result': True,
                        'data': {'model_id': 'D881079E1ED14FB'}
                    }
                }

        Status:

                preprocess: Search is preprocessing data for traing
                started: Search is in progress
                completed: Search is completed
                interrupted: Search was interrupted
                
        Examples:
            .. code-block:: python

                ctx = Context()
                model = Model(ctx, 'auger').deploy(model_id='D881079E1ED14FB', locally=True)
        """
        return self.__get_runner(locally).execute('deploy', model_id, locally)

    @show_result
    def predict(self, filename, model_id, threshold=None, locally=False, data=None, columns=None):
        """Predict results with new data against deployed model. Predictions are stored next to the file with data to be predicted on. The file name will be appended with suffix _predicted.

        Args:
            filename(str): The file with data to request predictions for.
            model_id(str): The deployed model id you want to use.
            threshold(float): For classification models only. This will return class probabilities with response.
            locally(bool): Predicts using a local model if True, on the Provider Cloud if False.
        
        Returns:
            Results for provider. ::

                {
                    'auger': {
                        'result': True,
                        'data': {'model_id': 'D881079E1ED14FB'}
                    }
                }


        Examples:
            .. code-block:: python

                ctx = Context()
                model = A2MLModel(ctx, 'auger').predict(filename=<path_to_file>/dataset.csv,model_id='D881079E1ED14FB',threshold=None,locally=False)
        """
        return self.__get_runner(locally).execute('predict', filename, model_id, threshold, locally, data, columns)

    @show_result
    def actual(self, filename, model_id):
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
                



        Args:
            filename(str): The file with data to request predictions for.
            model_id(str): The deployed model id you want to use.
        
        Returns:
            Results for each provider. ::

                {
                    'auger': {
                        'result': True,
                        'data': ''
                    }
                }


        Examples:
            .. code-block:: python

                ctx = Context()
                model = A2MLModel(ctx, 'auger, azure').actual(filename=<path_to_file>/dataset_actuals.csv,model_id='D881079E1ED14FB')
        """
        return self.runner.execute('actual', filename, model_id)

    def __get_runner(self, locally):
        if locally:
            return self.local_runner()
        else:
            return self.runner
