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
    source:
    exclude:
    target:
    model_type: 
    experiment:
      cross_validation_folds:
      max_total_time:
      max_eval_time:
      max_n_trials:
      use_ensemble:
      validation_data:


Provider Specfic
----------------

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
      metric: accuracy
      trials_per_worker: 2
      class_weight:
      oversampling:
        name:
        params:
        sampling_strategy:
        k_neighbors:
    cluster:
      type:
      min_nodes:
      max_nodes:
      stack_version:


Azure
^^^^^

  - ``azure.yaml``

  .. code-block:: YAML

    dataset:
    experiment:
      name:
      run_id:
      metric:

    cluster:
      region:
      min_nodes:
      max_nodes:
      type:
      name:

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



A2ML can be configured in three different ways.

Architecture
============

A2ML Cloud (Coming Soon)
------------------------

.. image:: https://d2uakhpezbykml.cloudfront.net/images/a2ml-cloud.png
  :width: 50%
  :align: center
  :alt: A2ML cloud

Create one account in the |a2mlcloud| and let the cloud manage all the provider connections.

.. |a2mlcloud| raw:: html

   <a href="https://app.auger.ai/signup" target="_blank">A2ML Cloud</a>

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
