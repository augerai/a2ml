from a2ml.api.base_a2ml import BaseA2ML
from a2ml.api.utils.show_result import show_result

class A2MLExperiment(BaseA2ML):
    """Contains the experiment operations that interact with provider."""
    def __init__(self, ctx, provider=None):
        """Initializes a new a2ml experiment.

        Args:
            ctx (object): An instance of the a2ml Context.
            provider (str): The automl provider(s) you wish to run. For example 'auger,azure,google'. The default is None - use provider set in config.
        
        Returns:
            A2MLExperiment object

        Examples:
            .. code-block:: python

                ctx = Context()
                model = A2MLExperiment(ctx, 'auger, azure')
        """
        super(A2MLExperiment, self).__init__(ctx, 'experiment')
        self.runner = self.build_runner(ctx, provider)

    @show_result
    def list(self):
        """List all of the experiments for the Project specified in the .yaml.

        Note:
            You will need to user the `iter <https://www.programiz.com/python-programming/methods/built-in/iter>`_ function to access the dataset elements.
        
        Returns:
            Results for each provider. ::

                {
                    'auger': {
                        'result': True,
                        'data': {
                            'experiments': <object> 
                        }
                    }
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                experiment_list = A2MLExperiment(ctx, 'auger, azure').list()
                for provider in ['auger', 'azure']
                    if experiment_list[provider].result is True:
                        for experiment in iter(experiment_list[provider].data.datasets):
                            ctx.log(experiment.get('name'))
                    else:
                        ctx.log('error %s' % experiment_list[provider].data)
        """
        return self.runner.execute('list')

    @show_result
    def start(self):
        """Starts experiment/s for selected dataset. If the name of experiment is not set in context config, new experiment will be created, otherwise an existing experiment will be run.
        
        Returns:
            Results for each provider. ::

                {
                    'auger': {
                        'result': True,
                        'data': {
                            'experiment_name': <experiment_name>,
                            'session_id': <session_id>
                        }
                    }
                }
        
        Examples:
            .. code-block:: python

                ctx = Context()
                experiment = A2MLExperiment(ctx, providers).start()

        """
        return self.runner.execute('start')

    @show_result
    def stop(self, run_id=None):
        """Stops runninng experiment/s.

        Args:
            run_id (str): The run id for a training session. A unique run id is created for every train. If set to None default is last experiment train.

        Returns:
            Results for each provider. ::

                {
                    'auger': {
                        'result': True,
                        'data': {
                            'stopped': <experiment_name>
                        }
                    }
                }
        
        Examples:
            .. code-block:: python

                ctx = Context()
                experiment = A2MLExperiment(ctx, providers).stop()

        """
        return self.runner.execute('stop', run_id)

    @show_result
    def leaderboard(self, run_id):
        """The leaderboard of the currently running or previously completed experiment/s.

        Args:
            run_id (str): The run id for a training session. A unique run id is created for every train. If set to None default is last experiment train.
        
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
                leaderboard = A2MLExperiment(ctx, 'auger, azure').leaderboard()
                for provider in ['auger', 'azure']
                if leaderboard[provider].result is True:
                    for entry in iter(leaderboard[provider].data.leaderboard):
                        ctx.log(entry['model id'])
                        ctx.log('status %s' % leaderboard[provider].data.status)
                else:
                    ctx.log('error %s' % leaderboard[provider].data)

        """
        return self.runner.execute('leaderboard', run_id)

    @show_result
    def history(self):
        """The history of the currently running or previously completed experiment/s.

        Note:
            You will need to user the `iter <https://www.programiz.com/python-programming/methods/built-in/iter>`_ function to access the dataset elements.
        
        Returns:
            Results for each provider. ::

                 {
                    'auger': {
                        'result': True,
                        'data': {
                            'history': <object>
                        }
                    }
                }
        
        Examples:
            .. code-block:: python

                ctx = Context()
                history = A2MLExperiment(ctx, 'auger, azure').history()
                for provider in ['auger', 'azure']
                if history[provider].result is True:
                    for run in iter(history[provider].data.history):
                    ctx.log("run id: {}, status: {}".format(
                        run.get('id'),
                        run.get('status')))
                else:
                    ctx.log('error %s' % history[provider].data)

        """
        return self.runner.execute('history')
