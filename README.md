# a2ml - Automation of AutoML
Th A2ML ("Automate AutoML") project is a set of scripts to automate Automated Machine Learning tools from multiple vendors. The intention is to provide a common API for all Cloud AutoML vendors.  Data scientists can then train their datasets against multiple AutoML models to get the best possible predictive model.  May the best "algorithm/hyperparameter search" win.

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

Since ITEDPR is hard to remember we refer to this pipeline by its conveniently mnemonic anagram: "PREDIT" (French
for "predict"). The A2ML project provides classes which implement this pipeline for various Cloud AutoML providers
and a command line interface that invokes stages of the pipeline.

## A2ML Classes
The A2ML Model class in A2ML.PY abstracts out the PREDICT (ICTEDPR) pipeline.  Implementations are provided for Google Cloud AutoML Tables (GCModel) and Auger.AI (Auger).   We will be adding support for Microsoft Azure AutoML soon. If you want to add support for another AutoML provider of your choice.  Implement a child class of Model as shown below (replacing each "pass" with your own code.

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

## The A2ML CLI

This is the command line interface for the A2ML classes. It provides command line options
for each stage in the PREDICT Pipeline.

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
$ a2ml command --help
```

## Configuration Options

After a new A2ML application created, application configuration stored in CONFIG.YAML. The options available include:
* name - the name of the experiment
* provider - the AutoML provider: GC (for Google Cloud), AZ (for Microsoft Azure), or Auger
* project - the name of the project in the AutoML provider's environment
* region - the compute region on the cloud provider
* source - the CSV file to train with
* dataset_id - the Google Cloud dataset after source import
* target - the feature which is the target
* exclude - features to exclude from the model
* metric - how to measure the accuracy of the model
* budget - the time budget in milliseconds to train 

Here is an example CONFIG.YAML for Google Cloud AutoML:

```
name: moneyball
provider: GC
project: automl-test-237311
region: us-central1
source: gs://moneyball/baseball.csv
dataset_id: TBL4772768869943083008
target: RS
exclude: Team,League,Year
metric: MINIMIZE_MAE
budget: 3600
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
$ pip install -e .[all]
```

Running tests and getting test coverage:

```
$ pytest pytest --cov='a2ml' --cov-report html tests/  
```
