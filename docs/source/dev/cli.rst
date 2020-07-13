**************
A2ML CLI
**************

The command line is a convenient way to start an A2ML project even if you plan to use the API.

Creating a New A2ML Project
===========================

Create a new A2ML project with the ``new`` command by supplying a project name. A2ML will create a directory which has a default set of configuration files that can be more specifically configured.

.. code-block:: bash

  $ a2ml new test_app

Configuring Your A2ML Project
=============================

To use the Python API or the command line interface for a specific PREDIT pipeline, configure the project first.

This includes both general options that apply to all vendors and vendor specific options in separate YAML files.

**All Vendors**

  - ``config.yaml``

  .. code-block:: YAML

    name: the name of the project
    provider: the AutoML provider. **GC (for Google Cloud)**, **AZ (for Microsoft Azure)**, or **Auger**
    source: the CSV or Parquet file to train with. Can be a local file path (for Auger or Azure). Can be a hosted file URL. Can be URL for Google Cloud Storage ("gs://...") for Google Cloud AutoML.
    source_format: csv(default), parquet. Set it if source is url or file has no extension
    exclude: features from the dataset to exclude from the model
    target: the feature which is the target
    model_type: Can be regression, classification or timeseries
    budget: the time budget in milliseconds to train

**Vendor Specfic**

 - ``auger.yaml``
 - ``azure.yaml``
 - ``google.yaml``

 .. code-block:: YAML

    region: the region for the AutoML providers compute clusters, each vendor has different names for their regions
    metric: how to measure the accuracy of the model to perform the search of algorithms, each vendor has different names for their regions

Examples
--------

Here is an example with options that apply to all AutoML providers:

**config.yaml**

.. code-block:: YAML

  source: ./moneyball/train.csv
  exclude: Team,League,Year
  target: RS
  model_type: regression
  experiment:
    cross_validation_folds: 5
    max_total_time: 60
    max_eval_time: 5
    max_n_trials: 10
    use_ensemble: true

**azure.yaml**

.. code-block:: YAML

  experiment:
    metric: r2_score

  cluster:
    region: eastus2
    name: cpucluster
    min_nodes: 0
    max_nodes: 4
    type: STANDARD_D2_V2

  file_share:
  account_name:
  account_key:
  dataset: train.csv
  
**google.yaml**

.. code-block:: YAML

  region: us-central1
  metric: MINIMIZE_MAE
  project: automl-test-237311
  dataset_id: TBL1889796605356277760
  operation_id: TBL2145477039279308800
  operation_name: projects/291533092938/locations/us-central1/operations/TBL4473943599746121728
  model_name: projects/291533092938/locations/us-central1/models/TBL1517370026795991040

**auger.yaml**

.. code-block:: YAML

  project: moneyball
  dataset: train.csv

  experiment:
    cross_validation_folds: 5
    max_total_time: 60
    max_eval_time: 1
    max_n_trials: 10
    use_ensemble: true
    metric: f1_macro

A2ML CLI Commands
=================

Below are the full set of commands provided by A2ML. Command line options are provided for each stage in the PREDIT Pipeline.

  .. code-block:: bash

    $ a2ml [OPTIONS] COMMAND [ARGS]...

**Commands**

  - **new** *Create new A2ML application*.
  - **import** *Import data for training*.
  - **train** *Train the model*.
  - **evaluate** *Evaluate models after training*.
  - **deploy** *Deploy trained model*.
  - **predict** *Predict with deployed model*.
  - **review** *Review specified model info*.
  - **project** *Project(s) management*.
  - **dataset** *Dataset(s) management*.
  - **experiment** *Experiment(s) management*.
  - **model** *Model(s) management*.

To get detailed information on available options for each command, please run:

  .. code-block:: bash

    $ a2ml command --help

