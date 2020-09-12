*************
Configuration
*************

Files
=====
To use the Python API or the command line interface for a specific PREDIT pipeline, configure the project first.

This includes both general options that apply to all providers and provider specific options in separate YAML files.

All Providers
-------------

  - ``config.yaml``

  .. code-block:: YAML

    name:
    providers:
    use_auger_cloud: 
    source: 
    exclude: 
    target: 
    model_type:
    experiment:
      metric:    
      cross_validation_folds: 
      max_total_time: 
      max_eval_time: 
      max_n_trials: 
      use_ensemble: 
      validation_source: 

  **Attributes**

    * **name** The project name.
    * **providers** List of providers: auger, google, azure.
    * **use_auger_cloud** Use Auger Cloud for all providers true | false
    * **source** Local file name or remote url to the data source file.
    * **exclude** List of columns to be excluded from the training data.
    * **target** Target column name.
    * **model_type**  Model type: classification|regression|timeseries.
    * **experiment.metric**  Score used to optimize ML model.

      * **Classification** accuracy, precision_weighted, roc_auc_ovr_weighted, norm_macro_recall, average_precision_score_weighted
      * **Auger only: Classification** f1_macro, f1_micro, f1_weighted, neg_log_loss, precision_macro, precision_micro, recall_macro, recall_micro, recall_weighted
      * **Auger only: Binary Classification** average_precision, f1, f1_macro, f1_micro, f1_weighted, neg_log_loss, precision, precision_macro, precision_micro, recall, recall_macro, recall_micro, recall_weighted, roc_auc, cohen_kappa_score, matthews_corrcoef
      * **Regression and/or Time Series** spearman_correlation, r2, normalized_mean_absolute_error, normalized_root_mean_squared_error
      * **Auger only: Regression and/or Time Series** explained_variance, neg_median_absolute_error, neg_mean_absolute_error, neg_mean_squared_error, neg_mean_squared_log_error, neg_rmsle, neg_mase, mda, neg_rmse

    * **experiment.cross_validation_folds** Number of folds used for k-folds validation of individual trial.
    * **experiment.max_total_time** Maximum time to run experiment in minutes.
    * **experiment.max_eval_time** Maximum time to run individual trial in minutes.
    * **experiment.max_n_trials** Maximum trials to run to complete experiment.
    * **experiment.use_ensemble** Try to improve model performance by creating ensembles from the trial models true | false.
    * **experiment.validation_source** Path to validation dataset. If not set your source dataset will be split to validate.


Provider Specfic
----------------

.. |oversampling| raw:: html

  <a href="https://imbalanced-learn.readthedocs.io/en/stable/api.html#module-imblearn.over_sampling" target="_blank">oversampling</a>


Currently a2ml supports Auger, Azure, and Google providers.


Auger
^^^^^
 
  - ``auger.yaml``

  .. code-block:: YAML

    dataset:
    experiment:
      name:
      experiment_session_id:
      time_series:
      label_encoded: []
      estimate_trial_time: False
      trials_per_worker: 2
      class_weight:
      oversampling:
        name:
        params:
          sampling_strategy:
          k_neighbors:


  **Attributes**
    
    * **dataset** Name of the DataSet on Auger Cloud.
    * **experiment.name** Latest experiment name.
    * **experiment.experiment_session_id** Latest experiment session.
    * **experiment.time_series** Time series feature. If Data Source contains more then one DATETIME feature you will have to explicitly specify feature to use as time series.
    * **experiment.label_encoded** List of columns which should be used as label encoded features.
    * **estimate_trial_time** Use it if you have a lot of timeouted trials. Set it to True will predict the training time of each individual model to avoid timeouts. Default is False.
    * **trials_per_worker** Use it if you have a lot of failed trials. Set it to value < 8 to give trial fit process more memory. Default is None.
    * **class_weight** Balanced | Balanced Subsample. Class Weights associated with classes. If None, all classes are supposed to have weight one. The Balanced mode automatically adjusts weights inversely proportional to class frequencies in the input data. The Balanced Subsample mode is the same as Balanced except that weights are computed based on the bootstrap sample for every tree grown.
    * **oversampling.name** SMOTE, RandomOverSampler, ADASYN, SMOTEENN, SMOTETomek. Oversampling Methods to adjust the class distribution of a data set
    * **oversampling.params.sampling_strategy**  auto, minority, majority, not minority, not majority, all
    * **oversampling.params.k_neighbors**  Integer value of k_neighbors

    .. note::

      For more information on |oversampling|
    
Azure
^^^^^

  - ``azure.yaml``

  .. code-block:: YAML

    dataset:
    experiment:
      name:
      run_id:

    cluster:
      region:
      min_nodes:
      max_nodes:
      type:
      name:

  **Attributes**

    * **dataset** Name of the DataSet on Azure Cloud.
    * **experiment.name** Latest experiment name.
    * **experiment.run_id** Latest experiment run.
    * **cluster.region** Name of cluster region. For example: eastus2
    * **cluster.min_nodes** Minimum number of nodes allocated for cluster. Minimum is 0. 
    * **cluster.max_nodes** Maximum number of nodes allocated for cluster.
    * **cluster.type** Cluster node type. For example: STANDARD_D2_V2. Please read Azure documentation for available options and prices.
    * **cluster.name** Name of existing cluster or new one to create.
  

Google
^^^^^^

  - ``google.yaml``

  .. code-block:: YAML

    project: 
    experiment: 
      metric:
    cluster: 
      region:
    gsbucket:

  **Attributes**

    * **project** Name of the Project on Google Cloud.
    * **experiment.metric** Metric used to build Model
    * **cluster.region** 
    * **gsbucket**


A2ML can be configured in three different ways.

Architecture
============

Auger Cloud
------------------------

.. image:: https://d2uakhpezbykml.cloudfront.net/images/a2ml-cloud.png
  :width: 50%
  :align: center
  :alt: A2ML cloud

Create one account in the |a2mlcloud| and let the cloud manage all the provider connections.

.. |a2mlcloud| raw:: html

   <a href="https://app.auger.ai/signup" target="_blank">Auger Cloud</a>

A2ML Local
----------

Direct Provider Connection
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: https://d2uakhpezbykml.cloudfront.net/images/a2ml-client-direct.png
  :width: 50%
  :align: center
  :alt: A2ML client direct providers

Directly configure the provider(s) and connect to them from the a2ml client.

Server Provider Connection
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: https://d2uakhpezbykml.cloudfront.net/images/a2ml-client-server.png
  :width: 50%
  :align: center
  :alt: A2ML cloud

Host a server which manages provider connections. The a2ml client would then point to the server.
