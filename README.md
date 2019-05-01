# a2ml - Automation of AutoML
Th A2ML ("Automate AutoML") project is a set of scripts to automate Automated Machine Learning tools from multiple vendors. The intention is to provide a common API for all Cloud AutoML vendor.  Data scientists can then train their datasets against multiple
AutoML models to get the best possible predictive model.  May the best 
"algorithm/hyperparameter search" win.

## The PREDICT Pipeline
Every AutoML vendor has their own API to manage the datasets and create and
manage predictive models.  They are similar but not identical APIs.  But they share a
common set of stages:
* Importing data for training
* Configuring the training parameters (targets, features, algorithms to consider)
* Train models with multiple algorithms and hyperparameters
* Evaluate model performance and choose one or more for deployment
* Deploy selected models
* Predict results with new data against deployed models
* Review performance of deployed models 

Since ICTEDPR is hard to remember we refer to this pipeline as: PREDICT.  The A2ML
project provides a command line interface and APIs that implement this pipeline. 

## GC_A2ML

This is the current primary functional script.  It provides command line options
for each stage in the PREDICT Pipeline for the Google Cloud AutoML service.  Support for other Cloud AutoML providers with the same API will be added shortly (specifically Microsoft Azure AutoML and DeepLearn's Auger.AI service). 

usage: GC_A2ML [-h] [-P] [-R] [-E] [-D] [-I] [-C] [-T] [-p PROJECT]
               [-d DATASET] [-m MODEL] [-i MODEL_ID] [-s SOURCE] [-t TARGET]
               [-b BUDGET] [-x EXCLUDE] [-z SCORE_THRESHOLD]

A2ML - Automating AutoML. 
    
Uppercase P-R-E-D-I-C-T options run parts of the pipeline:
* -P, --PREDICT         Predict with deployed model
* -R, --REVIEW          Review specified model info
* -E, --EVALUATE        Evaluate models after training
* -D, --DEPLOY          Deploy model
* -I, --IMPORT          Import data for training
* -C, --CONFIGURE       Configure model options before training
* -T, --TRAIN           Train the model

Lowercase options set project, dataset, model and others that span pipeline stages .
* -p PROJECT, --project <Google Cloud project ID>, overrides PROJECT_ID env var
* -d DATASET, --dataset <Google Cloud dataset ID>
* -m MODEL, --model <Model name>
* -i MODEL_ID, --model_id <Model ID>
* -s SOURCE, --source <Source file path for loading dataset or prediction CSV>
* -t TARGET, --target <Target column from dataset>
* -b BUDGET, --budget <Max training time in seconds>
* -x EXCLUDE, --exclude <Excludes given columns from model>
* -z SCORE_THRESHOLD, <Score threshold for prediction>

## Example Pipeliine
A typical usage of the PREDICT pipeline would be successive invocations of the followiing stages:
* IMPORT 
python gc_a2ml.py -I -d TBL6121667327084724224 -m MoneyBall -s baseball.csv -p automl-test-237311 
* CONFIGURE
* TRAIN
python gc_a2ml.py -T -d TBL6121667327084724224 -m MoneyBall -t RS -p automl-test-237311 -xTeam,League,Year
* EVALUATE
python gc_a2ml.py -E -i TBL7363086323588005888  -p automl-test-237311 
* DEPLOY
python gc_a2ml.py -D -i TBL7363086323588005888 -p automl-test-237311 
* PREDICT
python gc_a2ml.py -P -i TBL9182681310534041600  -p automl-test-237311 -s baseball_predict.csv
* REVIEW