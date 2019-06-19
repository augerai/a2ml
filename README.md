# a2ml - Automation of AutoML
Th A2ML ("Automate AutoML") project is a Python API and set of command line tools to automate Automated Machine Learning tools from multiple vendors. The intention is to provide a common API for all Cloud-oriented AutoML vendors.  Data scientists can then train their datasets against multiple AutoML models to get the best possible predictive model.  May the best "algorithm/hyperparameter search" win.

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

The command line is a convenient way to start an A2ML project even if you plan to use 
the API.  

### Creating a New A2ML Project
Specifically, you can start a new A2ML project with the new command supplying a project name.  A2ML will create a directory which has a default set of configuration files that you can then more specifically configure. 

```
a2ml new test_appp
```
### Configuring Your A2ML Project

Before you use the Python API or the command line interface for the specific PREDIT pipeline steps you will need to configure your particular project (although this can 
and probably should be after the "new" command above). This includes both general options that apply to all AutoML providers and provider specific options in separate YAML files.  

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

```
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
```
project: automl-test-237311 # the project name on the Google infrastructure
experiment:
  metric: MINIMIZE_MAE # how to score accuracy
cluster:
  region: us-central1 # what's the compute region (little else can be configured on Google now)
gsbucket: gs://a2ml  # location of source data on Google Cloud infrastrure
```

#### AUGER.YAML
Here's an example configuration file for Auger.AI 
``` auger.yaml
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

#### AZURE.YAML

Below is a sample Azure configuration file for this same project.

```
experiment:
  cross_validation_folds: 5
  max_total_time: 60
  max_n_trials: 10
  iteration_timeout_minutes: 1
  metric: spearman_correlation

cluster: 
  region: eastus2
  name: a2ml
  min_nodes: 0
  max_nodes: 4
  type: STANDARD_D2_V2

workspace: autoautoml
resource_group: autoautoml
```

Once you project is configured with these YAML files you can skip ahead to the 
[Using the A2ML API](#using-the-a2ml-api) section if you want to start using the
A2ML Python API instead of the CLIcd . 

### The A2ML CLI Commands Available
Below are the full set of commands provided by A2ML. Command line options are provided for each stage in the PREDIT Pipeline.

Usage:
```
$ a2ml [OPTIONS] COMMAND [ARGS]...
```
Commands:
* new       Create new A2ML application.
* import    Import data for training.
* train     Train the model.
* evaluate  Evaluate models after training.
* deploy    Deploy trained model.
* predict   Predict with deployed model.
* review    Review specified model info.

To get detailed information on available options for each command, please run:

```

## Using the A2ML API
After you have configured the YAML files as shown above (whether from scratch 
or using the templates provided by "a2ml new") you can use the API to 
import, train, evaluate, deploy, predict and review (the PREDIT pipeline).

In your Python code, you will first need retrieve the configuration by referring
to a Context() object.  Then you can create a client for the A2ML class. 
From that client object you will execute the various PREDIT pipeline methods
(starting from "import_data". Below is example Python code for this. 

```
    import os
    from a2ml.api.a2ml import A2ML
    from a2ml.api.google.a2ml import GoogleA2ML
    from a2ml.api.utils.context import Context
    self.ctx = Context()
    a2ml = GoogleA2ML(self.ctx)
    result = a2ml.import_data()
```

## Development Setup

We strongly recommend to install Python virtual environment:

```
$ pip install virtualenv virtualenvwrapper
```

Clone A2ML:

```
$ git clone https://github.com/deeplearninc/a2ml.git
```

Setup dependencies and A2ML command line:

```
$ pip install -e ".[all]"
```

Running tests and getting test coverage:

```
$ pytest pytest --cov='a2ml' --cov-report html tests/  
```

## Implementing A2ML for Another AutoML Provider
The A2ML Model class in A2ML.PY abstracts out the PREDIT (ITEDPR) pipeline.  Implementations are provided for Google Cloud AutoML Tables (GCModel), Azure AutoML (AZModel) and Auger.AI (Auger). If you want to add support for another AutoML provider of your choice, implement a child class of Model as shown below (replacing each "pass" with your own code.

```
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
