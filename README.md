# a2ml - Automation of AutoML
The A2ML ("Automate AutoML") project is a Python API and set of command line tools to automate Automated Machine Learning tools from multiple vendors. The intention is to provide a common API for all Cloud-oriented AutoML vendors.  Data scientists can then train their datasets against multiple AutoML models to get the best possible predictive model.  May the best "algorithm/hyperparameter search" win.

## The PREDIT Pipeline
Every AutoML vendor has their own API to manage the datasets and create and
manage predictive models.  They are similar but not identical APIs.  But they share a
common set of stages:
* Importing data for training
* Train models with multiple algorithms and hyperparameters
* Evaluate model performance and choose one or more for deployment
* Deploy selected models
* Predict results with new data against deployed models
* Review performance of deployed models

Since ITEDPR is hard to remember we refer to this pipeline by its conveniently mnemonic anagram: "PREDIT" (French for "predict"). The A2ML project provides classes which implement this pipeline for various Cloud AutoML providers
and a command line interface that invokes stages of the pipeline.

## Command Line Interface

The command line is a convenient way to start an A2ML project even if you plan to use the API.  

### Creating a New A2ML Project
Specifically, you can start a new A2ML project with the new command supplying a project name.  A2ML will create a directory which has a default set of configuration files that you can then more specifically configure.

```sh
$ a2ml new test_app
```

### Configuring Your A2ML Project

Before you use the Python API or the command line interface for the specific PREDIT pipeline steps you will need to configure your particular project. This includes both general options that apply to all vendors and vendor specific options in separate YAML files.  

After a new A2ML application is created, application configuration for all providers are stored in CONFIG.YAML. The options available include:
* name - the name of the project
* provider - the AutoML provider: GC (for Google Cloud), AZ (for Microsoft Azure), or Auger
* source - the CSV file to train with. Can be a local file path  (for Auger or Azure). Can be a hosted file URL.  Can be URL for Google Cloud Storage ("gs://...") for
Google Cloud AutoML.  
* exclude - features from the dataset to exclude from the model
* target - the feature which is the target
* model_type - Can be regression, classification or timeseries
* budget - the time budget in milliseconds to train

Examples of options which apply to specific vendors include:
* region - the region for the AutoML providers compute clusters, each vendor has different names for their regions
* metric - how to measure the accuracy of the model to perform the search of algorithms, each vendor has different names for their regions

Here is an example CONFIG.YAML with options that apply to all AutoML providers:

```yaml
name: moneyball
providers: google,azure,auger
source: gs://moneyball/baseball.csv
exclude: Team,League,Year
target: 'RS'
model_type: regression
budget: 3600
```

#### GOOGLE.YAML Configuration
Here is an example specific configuration file (google.yaml) for Google AutoML for this project:
```yaml
region: us-central1
metric: MINIMIZE_MAE
project: automl-test-237311
dataset_id: TBL1889796605356277760
operation_id: TBL2145477039279308800
operation_name: projects/291533092938/locations/us-central1/operations/TBL4473943599746121728
model_name: projects/291533092938/locations/us-central1/models/TBL1517370026795991040
```

#### AUGER.YAML
Here's an example configuration file for Auger.AI

```yaml
project: test_app
dataset: some_test_data

experiment:
  cross_validation_folds: 5
  max_total_time: 60
  max_eval_time: 1
  max_n_trials: 10
  use_ensemble: true
  metric: f1_macro

cluster:
  type: high_memory
  min_nodes: 1
  max_nodes: 4
  stack_type: experimental
```

Once your project is configured with these YAML files you can skip ahead to the
[Using the A2ML API](#using-the-a2ml-api) section if you want to start using the
A2ML Python API.

### The A2ML CLI Commands Available
Below are the full set of commands provided by A2ML. Command line options are provided for each stage in the PREDIT Pipeline.

Usage:
```sh
$ a2ml [OPTIONS] COMMAND [ARGS]...
```
Commands:
* new        Create new A2ML application.
* import     Import data for training.
* train      Train the model.
* evaluate   Evaluate models after training.
* deploy     Deploy trained model.
* predict    Predict with deployed model.
* review     Review specified model info.
* project    Project(s) management
* dataset    Dataset(s) management
* experiment Experiment(s) management
* model      Model(s) management

To get detailed information on available options for each command, please run:

```sh
$ a2ml command --help
```

## Using the A2ML API from Python
After you have configured the YAML files as shown above (whether from scratch
or using the templates provided by "a2ml new") you can use the API to
import, train, evaluate, deploy, predict and review (the PREDIT pipeline).  These configured files should be in the directory you are running from.

In your Python code, you will first need retrieve the configuration by referring
to a Context() object.  Then you can create a client for the A2ML class.
From that client object you will execute the various PREDIT pipeline methods
(starting from "import_data"). Below is example Python code for this.

  ```python
  import os
  from a2ml import A2ML, Context
  ctx = Context()
  a2ml = A2ML(ctx, 'auger, azure')
  result = a2ml.import_data()
  ```

## Base Classes

### a2ml.api.utils.Context
Context provides environment to run A2ML Experiments and Models:
- loads Credentials;
- loads app settings from .yaml files and provides access to these settings
to A2ML classes and business objects;
- provides logging interface to all A2ML classes and business objects.

### a2ml.api.A2ML - A2ML PREDIT API

- **A2ML(context, providers = None)** - constructs A2ML PREDIT instance.
  - context - instance of a2ml Context
  - providers - list of providers (auger, azure, etc.)

- **import_data()** - Importing data for training

  Source should be set in config (TBD - pass source as parameter)

  Returns:
  ```
    {
      provider_name:
        {
          result: True|False,
          data: {created: dataset_name}|error
        }
    }
  ```

- **train()** - Train models with multiple algorithms and hyperparameters

  Returns:
  ```
    {
      provider_name:
        {
          result: True|False,
          data: {'eperiment_name': eperiment_name, 'session_id': session_id}|error
        }
    }
  ```

- **evaluate(run_id = None)** - Evaluate model performance and choose one or
more for deployment

  Returns:
  ```
    {
      provider_name:
        {
          result: True|False,
          data: {'run_id': run_id, 'leaderboard': iterator, 'status': status}|error
        }
    }
  ```
  Status:  
  - preprocess - Search is preprocessing data for traing;
  - started - Search is in progress;
  - completed - Search is completed;
  - interrupted - Search was interrupted.

  Leaderboard entry:
  - 'model id': model id
  - score name: score value
  - 'algorithm': algorithm name

- **deploy(model_id, locally=False)** - Deploy selected model
  - model_id - id of the model from the any Experiment leaderboard
  - locally - deploys model locally if True, on Provider Cloud if False; optional,
    default is False.

  Returns:
  ```
    {
      provider_name:
        {
          result: True|False,
          data: {'model_id': model_id}|error
        }
    }
  ```

- **predict(filename, model_id, threshold=None, locally=False)** - Predict
results with new data against deployed model.
Predictions stored next to the file with data to be
predicted on; file name will be appended with suffix `_predicted`.
  - filename - file with data to be predicted
  - model_id - id of the deployed model
  - threshold - prediction threshold
  - locally - if True predict using locally deployed model, predict using model
    deployed on Provider Cloud

  Returns:
  ```
    {
      provider_name:
        {
          result: True|False,
          data: {'predicted': dataset_predicted.csv}|error
        }
    }
  ```
- **review** - Review performance of deployed model(s)
  TBD

### a2ml.api.A2MLProject
Project interface to A2ML Provider Projects.

- **A2MLProject(context, providers)** - constructs Project instance.
  - context - instance of a2ml Context
  - providers - list of providers (auger, azure, etc.)

- **list()** - lists all Projects for the specified providers.

  Returns: dictionary with iterators to the list of Projects for each provider.
  ```
    {
      provider_name:
        {
          result: True|False,
          data: {projects: iterator}|error
        }
    }
  ```

  Example:
  ```
  ctx = Context()
  rv = A2MLProject(ctx, 'auger, azure').list()
  for provider in ['auger', 'azure']
    if rv[provider].result is True:
      for project in iter(rv[provider].data.projects):
        ctx.log(project.get('name'))
    else:
      ctx.log('error %s' % rv[provider].data)
  ```

- **create(project_name)** - creates Project on Provider Clouds.

  Returns:
  ```
  {
    provider_name:
      {
        result: True|False,
        data: {'created': project_name}|error
      }
  }
  ```

  Example:
  ```
  ctx = Context()
  rv = A2MLProject(ctx, 'auger, azure').create(new_project_name)  
  ```

- **delete(project_name)** - deletes Project on Provider Clouds.

  Returns:
  ```
  {
    provider_name:   
      {
        result: True|False,
        data: {'deleted': project_name}|error
      }
  }
  ```

  Example:
  ```
  ctx = Context()
  rv = A2MLProject(ctx, 'auger, azure').delete(existing_project_name)
  ```
- **select(project_name)** - sets project name in Context

- **properties()** - TBD

### a2ml.api.A2MLDataset
DataSet for training on Provider Cloud.

- **A2MLDataset(context, providers)** - constructs A2MLDataset instance.
  - context - instance of A2ML Context.
  - providers - list of providers (auger, azure, etc.)

- **list()** - lists all DataSets(s) for the Project specified in the .yaml.

  Returns: dictionary with iterators to the list of Projects for each provider.
  ```
    {
      provider_name:
        {
          result: True|False,
          data: {datasets: iterator}|error
        }
    }
  ```

  Example:
  ```
  ctx = Context()
  rv = A2MLDataset(ctx, 'auger, azure').list()
  for provider in ['auger', 'azure']
    if rv[provider].result is True:
      for dataset in iter(rv[provider].data.datasets):
        ctx.log(dataset.get('name'))
    else:
      ctx.log('error %s' % rv[provider].data)
  ```

- **create(source)** - creates new DataSet on Provider Cloud(s).

  - source - path to local or link to remote .csv or .arff file

  Returns:
  ```
    {
      provider_name:
        {
          result: True|False,
          data: {created: dataset_name}|error
        }
    }
  ```

  Example:
  ```
  ctx = Context()
  rv = DataSet(ctx, 'auger, azure').create('../iris.csv')
  if rv[provider].result is True:
    ctx.log('Created dataset %s' % rv[provider].data.created)
  else:
    ctx.log('error %s' % rv[provider].data)
  ```

- **delete(dataset_name)** - deletes DataSet on Provider Cloud(s).   

  Returns:
  ```
    {
      provider_name:
        {
          result: True|False,
          data: {deleted: dataset_name}|error
        }
    }
  ```

  Example:
  ```
  ctx = Context()
  DataSet(ctx, 'auger, azure').delete(dataset_name)
  ctx.log('Deleted dataset %s' % dataset_name)
  ```

- **select(dataset_name)** - sets dataset name in Context

- **properties()** - TBD

### a2ml.api.Experiment
Experiment searches for the best Model(s) for a given DataSet.

- **A2MLExperiment(context, providers)** - constructs Experiment instance.
  - context - instance of A2ML Context.
  - providers - list of providers (auger, azure, etc.)

- **list()** - list all Experiment(s)
  Returns: dictionary with iterators to the list of Projects for each provider.
  ```
    {
      provider_name:
        {
          result: True|False,
          data: {experiments: iterator}|error
        }
    }
  ```

  Example:
  ```
  ctx = Context()
  rv = A2MLExperiment(ctx, 'auger, azure').list()
  for provider in ['auger', 'azure']
    if rv[provider].result is True:
      for experiment in iter(rv[provider].data.experiments):
        ctx.log(experiment.get('name'))
    else:
      ctx.log('error %s' % rv[provider].data)
  ```

- **start()** - starts Experiment(s) with selected DataSet; If name of Experiment
is not set in Context config, new Experiment will be created, otherwise existing
Experiment will be run.  
  Returns:
  ```
    {
      provider_name:
        {
          result: True|False,
          data: {'eperiment_name': eperiment_name, 'session_id': session_id}|error
        }
    }
  ```

  Example:
  ```
  ctx = Context()
  rv = A2MLExperiment(ctx, providers).start()
  ```

- **stop()** - stops running Experiment(s).
  Returns:
  ```
    {
      provider_name:
        {
          result: True|False,
          data: {'stopped': experiment_name}|error
        }
    }
  ```

  Example:
  ```
  ctx = Context()
  rv = A2MLExperiment(ctx, providers).stop()
  ```

- **leaderboard(run_id)** - leaderboard of the currently running or
  previously completed experiment(s).

  Returns:
  ```
    {
      provider_name:
        {
          result: True|False,
          data: {'run_id': run_id, 'leaderboard': iterator, 'status': status}|error
        }
    }
  ```
  Status:  
  - preprocess - Search is preprocessing data for traing;
  - started - Search is in progress;
  - completed - Search is completed;
  - interrupted - Search was interrupted.

  Leaderboard entry:
  - 'model id': model id
  - score name: score value
  - 'algorithm': algorithm name

  Example:
  ```
  ctx = Context()
  rv = A2MLExperiment(ctx, 'auger, azure').leaderboard()
  for provider in ['auger', 'azure']
    if rv[provider].result is True:
      for entry in iter(rv[provider].data.leaderboard):
        ctx.log(entry['model id'])
      ctx.log('status %s' % rv[provider].data.status)
    else:
      ctx.log('error %s' % rv[provider].data)
  ```

- **history()** - history (leaderboards and settings) of the previous
  experiment runs. Returns iterator where each item is dictionary with properties
  of the previous Experiment runs.

  Returns:
  ```
    {
      provider_name:
        {
          result: True|False,
          data: {'history': iterator}|error
        }
    }
  ```

  Example:
  ```
  ctx = Context()
  rv = A2MLExperiment(ctx, 'auger, azure').history()
  for provider in ['auger', 'azure']
    if rv[provider].result is True:
      for run in iter(rv[provider].data.history):
        ctx.log("run id: {}, status: {}".format(
          run.get('id'),
          run.get('status')))
    else:
      ctx.log('error %s' % rv[provider].data)
  ```

- **properties()** - TBD

- **delete()** - TBD

### a2ml.api.A2MLModel
Deploys or predicts using one of the Models from the Project Experiment(s)
leaderboards.

- **A2MLModel(context, providers)** - constructs Model instance.
  - context - instance of A2ML Context.
  - providers - list of providers (auger, azure, etc.)

- **list()** - lists all deployed models for a Project;

- **deploy(model_id, locally)** - deploys selected model locally or on
  Provider Cloud. Returns deployed model id.
  - model_id - id of the model from the any Experiment leaderboard
  - locally - deploys model locally if True, on Provider Cloud if False; optional,
    default is False.

  Returns:
  ```
    {
      provider_name:
        {
          result: True|False,
          data: {'model_id': model_id}|error
        }
    }
  ```

  Example:
  ```
  ctx = Context()
  # deploys model locally
  rv = Model(ctx, providers).deploy(model_id, True)
  ```

- **predict(filename, model_id, threshold, locally)** - predicts using deployed
  model. Predictions stored next to the file with data to be
  predicted on; file name will be appended with suffix `_predicted`.
  - filename - file with data to be predicted
  - model_id - id of the deployed model
  - threshold - prediction threshold
  - locally - if True predict using locally deployed model, predict using model
    deployed on Provider Cloud

  Returns:
  ```
    {
      provider_name:
        {
          result: True|False,
          data: {'predicted': dataset_predicted.csv}|error
        }
    }
  ```

  Example:
  ```
  ctx = Context()
  rv = Model(ctx, project).predict('../irises.csv', model_id, None, True)
  # if rv[provider].result is True
  # predictions are stored in ../irises_predicted.csv
  ```

- **actual(filename, model_id)** - submit actuals

## Development Setup

We strongly recommend to install Python virtual environment:

```sh
$ pip install virtualenv virtualenvwrapper
```

Clone A2ML:

```sh
$ git clone https://github.com/augerai/a2ml.git
```

Setup dependencies and A2ML command line:

```sh
$ pip install -e ".[all]"
```

Running tests and getting test coverage:

```sh
$ tox
```

## Authentication with A2ML
Authentication with A2ML involves two parts. First, there is authentication between your client (whether it's the `a2ml` cli or the `a2ml` python API) and the service endpoint (either self-hosted or with Auger.AI). Second, there is authentication between the service endpoint and each provider. Note that in the case where you run A2ML locally, endpoint authentication is handled automatically. The table at the end of this section shows this in more detail.

### Authenticating with Auger.AI
You can login to the Auger.AI endpoint and provider with the `a2ml auth login` command.

```sh
a2ml auth login
```
You will be prompted for your Auger service user and password. You can also download your Auger credentials as a credentials.json file and refer to it with an AUGER_CREDENTIALS environment variable.

```sh
export AUGER_CREDENTIALS=~/auger_credentials.json
```
You can also put the path to credentials.json in an environment variable called AUGER_CREDENTIALS_PATH OR a key inside AUGER.YAML.  

The Auger service can manage your usage of Google Cloud AutoML or Azure AutoML for you. If you choose to set up your own endpoints, you must configure the underlying AutoML service corrrectly to be accessed from the server you are running from.  Here are abbreviated directions for that step for Google, Azure and Auger.

### Google Cloud AutoML
If you haven't run Google Cloud AutoML, set up a service account and save the credentials to a JSON file which you store in your project directory.  Then set up the GOOGLE_APPLICATION CREDENTIALS environment variable to point to the saved file.  For example:

```sh
export GOOGLE_APPLICATION_CREDENTIALS="/Users/adamblum/a2ml/automl.json"
```

For ease of use you can set up a default project ID to use with your project with the PROJECT_ID environment variable. For example:  

```sh
export PROJECT_ID="automl-test-237311"
```

Detailed instructions for setting up Google Cloud AutoML are [here](https://cloud.google.com/vision/automl/docs/before-you-begin)])    

### Azure AutoML
The Azure AutoML service allows credentials to be downloaded as a JSON file (such as a config.json file).  This should then be placed in a .azureml subdirectory of your project directory.  Be sure to include this file in your .gitignore:

```sh
**/.azureml/config.json
```

The Azure subscription ID can be set with the AZURE_SUBSCRIPTION_ID environment variable as in the following example.

```sh
export AZURE_SUBSCRIPTION_ID="d1b17dd2-ba8a-4492-9b5b-10c6418420ce"
```

### A2ML Authentication Components
The following shows which authentication components are necessary depending on your A2ML use case:

| | Auger.AI AutoML | Azure AutoML | Google Cloud AutoML |
| ------------- | ------------- |------------- |------------- |
| **Auger.AI Endpoint** | |  | | |
| Provider Credentials Required? | Yes  | No | No |
| |  | ||
| **Self-Hosted Endpoint** | | | |
| Provider Credentials Required? | Yes  | Yes | Yes |

## Python API

## Implementing A2ML for Another AutoML Provider
The A2ML Model class in A2ML.PY abstracts out the PREDIT (ITEDPR) pipeline.  Implementations are provided for Google Cloud AutoML Tables (GCModel), Azure AutoML (AZModel) and Auger.AI (Auger). If you want to add support for another AutoML provider of your choice, implement a child class of Model as shown below (replacing each "pass" with your own code.

```python
class AnotherAutoMLModel(Model):  
    def __init__(self):
        pass     
    def predict(self,filepath,score_threshold):
        pass
    def review(self):
        pass
    def evaluate(self):
        pass
    def deploy(self):
        pass
    def import_data(self):
        pass
    def train(self):
        pass
```
