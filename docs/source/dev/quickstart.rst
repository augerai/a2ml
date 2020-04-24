**********
Quickstart
**********

Please see :doc:`install` and :doc:`authentication` before starting.

Microsoft Azure and the Moneyball Dataset
=========================================

.. |moneyball| raw:: html

  <a href="https://www.kaggle.com/wduckett/moneyball-mlb-stats-19622012/download" target="_blank">Moneyball</a>


The following code shows how a2ml can be used with **Microsoft Azure** and **Auger** AutoML providers to perform a regression task against the |moneyball| dataset.


Dataset
-------

.. |detail| raw:: html

  <a href="https://towardsdatascience.com/moneyball-linear-regression-76034259af5e" target="_blank">detail</a>

|moneyball| is a baseball dataset from kaggle. The moneyball dataset can be used to build many different models as described in more |detail|.
The goal of this exercise is to find a highly accurate model to predict the number of runs scored\ **(RS)** a MLB team will have.

The dataset will be imported to Microsoft Azure and Auger AutoML providers without any data wrangling. 

A quick look at the data.

.. code-block:: python

  import pandas as pd

  df = pd.read_csv('baseball.csv')
  df.head()

.. image:: https://d2uakhpezbykml.cloudfront.net/images/baseball_dataset.png
  :width: 100%
  :align: center
  :alt: baseball dataset kaggle

The main features that will be used.

.. list-table:: baseball.csv
                :widths: 50 50
                :header-rows: 1

                * - feature
                  - description
                * - RS
                  - runs scored
                * - RS
                  - runs scored
                * - OBP
                  - on base percentage
                * - SLG
                  - slugging percentage
                * - BA
                  - batting average
                * - OOBP
                  - opponent’s on base percentage
                * - OSLG
                  - opponent’s slugging percentage
                * - W
                  - number of wins in that season

Project Setup
-------------

Inside of a terminal create a new a2ml project.

.. code-block:: bash

  $ a2ml new moneyball_project
  [config] Created project folder moneyball_project
  [config] To build your model, please do: cd moneyball_project && a2ml import && a2ml train

  $ cd moneyball_project
  $ ls 
  auger.yaml  azure.yaml config.yaml  google.yaml

To configure Microsoft Azure and Auger providers, open ``config.yaml``. 

.. code-block:: yaml
  :caption: config.yaml
  :name: config.yaml
  :emphasize-lines: 2,3,4,5,6

  name: moneyball_proj
  providers: auger,azure
  source: baseball.csv
  exclude: Team,League,Year,RankSeason,RankPlayoffs
  target: RS
  model_type: regression
  experiment:
    cross_validation_folds: 5
    max_total_time: 60
    max_eval_time: 5
    max_n_trials: 10
    use_ensemble: true

*The highlighted lines are where manual changes have been made.*

Import Dataset
--------------

To import the local |moneyball| baseball dataset.

.. code-block::
  :emphasize-lines: 27,31

  $ a2ml import
  [azure] Creating moneyball_proj
  UserWarning: The resource group doesn't exist or was not provided. AzureML SDK is creating a resource group=moneyball_proj-resources in location=eastus2 using subscription=28ca7f62-a275-4222-aaa1-c8e9ec93adbb.
  Deploying KeyVault with name moneybalkeyvaultf9fa9c80.
  Deploying StorageAccount with name moneybalstorage3643d4640.
  Deployed KeyVault with name moneybalkeyvaultf9fa9c80. Took 18.76 seconds.
  Deploying AppInsights with name moneybalinsights692c3d29.
  Deployed AppInsights with name moneybalinsights692c3d29. Took 24.88 seconds.
  Deployed StorageAccount with name moneybalstorage3643d4640. Took 23.02 seconds.
  Deploying Workspace with name moneyball_proj.
  Deployed Workspace with name moneyball_proj. Took 20.74 seconds.
  Called AzureBlobDatastore.upload_files
  Uploading an estimated of 1 files
  Uploading an estimated of 1 files
  Uploading baseball.csv
  Uploading baseball.csv
  Uploaded baseball.csv, 1 files out of an estimated total of 1
  Uploaded baseball.csv, 1 files out of an estimated total of 1
  Uploaded 1 files
  Uploaded 1 files
  Finished AzureBlobDatastore.upload with count=1.
  Could not load the run context. Logging offline
  [azure]  Created DataSet baseball.csv
  [auger]  Starting Project to process request...
  [auger]  Project status is deploying...
  Could not load the run context. Logging offline
  [azure]  Created DataSet baseball.csv
  [auger]  Project status is running...
  [auger]  DataSet status is processing...
  [auger]  DataSet status is processed...
  [auger]  Created DataSet baseball.csv

Notice how many assets were created in Microsoft Azure and Auger. Make sure to look for verification that import was successful.

.. code-block:: bash

  [azure]  Created DataSet baseball.csv
  [auger]  Created DataSet baseball.csv
  
.. note::

  If you are not authenticated with either provider run 

  .. code-block:: bash

    $ a2ml auth login

  or see the different :doc:`authentication` options and then run

  .. code-block:: bash

    $ a2ml import

  Only the remaining import steps will be run.


Train
-----

Before training, update ``azure.yaml`` and ``auger.yaml`` to select a metric to evaluate models with.  **R2** will be used in this example.


.. code-block:: yaml
  :caption: azure.yaml
  :name: azure.yaml
  :emphasize-lines: 6
  

  subscription_id:
  dataset: baseball.csv
  experiment:
    name:
    run_id:
    metric: r2_score
  cluster:
    region: eastus2
    min_nodes: 0
    max_nodes: 2
    type: STANDARD_D2_V2
    name: a2ml-azure


.. code-block:: yaml
  :caption: auger.yaml
  :name: auger.yaml
  :emphasize-lines: 7

  dataset: baseball.csv
  experiment:
    name:
    experiment_session_id:
    time_series:
    label_encoded: []
    metric: r2
  cluster:
    type: standard
    min_nodes: 2
    max_nodes: 2
    stack_version: stable


To start training run

.. code-block:: bash

  $ a2ml train
  [azure]  Starting search on baseball.csv Dataset...
  Could not load the run context. Logging offline
  [azure]  Found compute target a2ml-azure ...
  Created a worker pool for first use
  [auger]  Created Experiment baseball.csv-experiment
  [auger]  Started Experiment baseball.csv-experiment search...
  [azure]  Started Experiment baseball-csv search...


Evaluate
--------
To view the realtime model results of a train, run.

.. code-block:: bash

  $ a2ml evaluate

  [auger]  Leaderboard for Run 0d8b32fedd073b8e
  [auger]  ----------------+---------+-------------------------------
  [auger]  model id        | r2      | algorithm
  [auger]  ----------------+---------+-------------------------------
  [auger]  FF4998552070427 | 0.9392  | SuperLearnerAlgorithmRegressor
  [auger]  ----------------+---------+-------------------------------
  [auger]  60A26A1DBC7543E | 0.9353  | LGBMRegressor
  [auger]  ----------------+---------+-------------------------------
  [auger]  Search is completed.
  [azure]  Leaderboard for Run AutoML_feca2e53-618b-4407-a17c-f119ba9d7578
  [azure]  ----------------------------------------------+----------------------------------+-------------------
  [azure]  model id                                      | algorithm                        | r2_score
  [azure]  ----------------------------------------------+----------------------------------+-------------------
  [azure]  AutoML_feca2e53-618b-4407-a17c-f119ba9d7578_9 | StackEnsemble                    | 0.9435518514990049
  [azure]  ----------------------------------------------+----------------------------------+-------------------
  [azure]  AutoML_feca2e53-618b-4407-a17c-f119ba9d7578_8 | VotingEnsemble                   | 0.942078490714301
  [azure]  ----------------------------------------------+----------------------------------+-------------------
  [azure]  AutoML_feca2e53-618b-4407-a17c-f119ba9d7578_0 | MaxAbsScaler,LightGBM            | 0.9338693722577552
  [azure]  ----------------------------------------------+----------------------------------+-------------------
  [azure]  AutoML_feca2e53-618b-4407-a17c-f119ba9d7578_1 | StandardScalerWrapper,LightGBM   | 0.9316232600551793
  [azure]  ----------------------------------------------+----------------------------------+-------------------
  [azure]  Status: Completed

Deploy
------

To deploy a specific model simply copy the **model id** from the leaderboard output and run.

.. code-block:: bash
  :emphasize-lines: 8,15

  $ a2ml deploy AutoML_feca2e53-618b-4407-a17c-f119ba9d7578_9
    
    6c664bf8-da13-41cd-ac87-d2f04ad77eb7 - CacheDriver:Cached token is expired at 2020-04-22 16:13:41.536177.  Refreshing
    6c664bf8-da13-41cd-ac87-d2f04ad77eb7 - TokenRequest:Getting a new token from a refresh token
    6c664bf8-da13-41cd-ac87-d2f04ad77eb7 - CacheDriver:Returning token refreshed after expiry.
    [auger]  Deploying model AutoML_feca2e53-618b-4407-a17c-f119ba9d7578_9
    Created a worker pool for first use
    [auger]  status: 404, body: {"meta":{"status":404,"request_params":{"trial_id":"AutoML_feca2e53-618b-4407-a17c-f119ba9d7578_9","token":"****","pipeline":{"trial_id":"AutoML_feca2e53-618b-4407-a17c-f119ba9d7578_9"},"is_review_model_enabled":true},"errors":[{"message":"There is no such Trial","error_type":"not_found"}]}} {"status": 404, "request_params": {"trial_id": "AutoML_feca2e53-618b-4407-a17c-f119ba9d7578_9", "token": "****", "pipeline": {"trial_id": "AutoML_feca2e53-618b-4407-a17c-f119ba9d7578_9"}, "is_review_model_enabled": true}, "errors": [{"message": "There is no such Trial", "error_type": "not_found"}]} on: POST /api/v1/pipelines {"trial_id": "AutoML_feca2e53-618b-4407-a17c-f119ba9d7578_9"}
    [azure]  Regestiring model: AutoMLfeca2e5369
    [azure]  Deploying AciWebservice automlfeca2e5369-service ...
    Warning, azureml-defaults not detected in provided environment pip dependencies. The azureml-defaults package contains requirements for the inference stack to run, and should be included.
    Running.....................................................
    Succeeded
    ACI service creation operation finished, operation "Succeeded"
    [azure]  automlfeca2e5369-service state Healthy

Notice the first highlighted line in the code block above outputs a not found error for the Auger provider.

.. code-block:: python

  status: 404, body: {"meta":{"status":404,"request_params":{"trial_id":"AutoML_feca2e53-618b-4407-a17c-f119ba9d7578_9","token":"****","pipeline":{"trial_id":"AutoML_feca2e53-618b-4407-a17c-f119ba9d7578_9"},"is_review_model_enabled":true},"errors":[{"message":"There is no such Trial","error_type":"not_found"}]}} {"status": 404, "request_params": {"trial_id": "AutoML_feca2e53-618b-4407-a17c-f119ba9d7578_9", "token": "****", "pipeline": {"trial_id": "AutoML_feca2e53-618b-4407-a17c-f119ba9d7578_9"}, "is_review_model_enabled": true}, "errors": [{"message": "There is no such Trial", "error_type": "not_found"}]} on: POST /api/v1/pipelines {"trial_id":"AutoML_feca2e53-618b-4407-a17c-f119ba9d7578_9"}

This is because a Microsoft Azure **model id** was selected.  To deploy a model to the Auger provider run.

.. code-block:: bash
  :emphasize-lines: 5

  $ a2ml deploy FF4998552070427 -p auger
  [auger]  Deploying model FF4998552070427
  [auger]  Pipeline status is packaging...
  [auger]  Pipeline status is ready...
  [auger]  Deployed Model on Auger Cloud. Model id is FF4998552070427

.. note::

  The **-p** argument allows a specific provider to be selected. At anytime to view a list of possible commands use **--help**

  .. code-block:: bash
    :emphasize-lines: 7

    $ a2ml deploy --help
    Usage: a2ml deploy [OPTIONS] MODEL_ID

      Deploy trained model.

    Options:
      -p, --provider TEXT  Cloud AutoML Provider.
      --locally            Download and deploy trained model locally.
      --help               Show this message and exit.

Predict
-------

To use the deployed model(s), pass a file of new observations with the target omitted.

.. code-block:: python

  import pandas as pd

  df = pd.read_csv('baseball_predict.csv')
  df.head()

.. image:: https://d2uakhpezbykml.cloudfront.net/images/baseball_predict.png
  :width: 100%
  :align: center
  :alt: baseball predict dataset

*Notice RS is not included in the file*

To initate predictions run.

.. code-block:: bash
  :emphasize-lines: 2

  $ a2ml predict -m AutoML_feca2e53-618b-4407-a17c-f119ba9d7578_9 -p azure baseball_predict.csv
  [azure]  Predictions are saved to <path_to>/moneyball_proj/baseball_predict_predicted.csv

*Notice a file has been created in the project directory* **baseball_predict_predicted.csv**

Displaying **baseball_predict_predicted.csv** shows that predictions for the target **RS** have been appended.
 
.. code-block:: python

  import pandas as pd

  df = pd.read_csv('baseball_predict_predicted.csv')
  df.head()

.. image:: https://d2uakhpezbykml.cloudfront.net/images/baseball_predicted.png
  :width: 100%
  :align: center
  :alt: baseball predicted dataset


  