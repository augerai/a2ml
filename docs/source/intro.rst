
A2ML - Automation of AutoML
---------------------------

The A2ML ("Automate AutoML") project is a Python API and set of command line tools to automate Automated Machine Learning tools from multiple vendors. The intention is to provide a common API for all Cloud-oriented AutoML vendors. Data scientists can then train their datasets against multiple AutoML models to get the best possible predictive model. May the best "algorithm/hyperparameter search" win.

The PREDIT Pipeline
===================
Every AutoML vendor has their own API to manage the datasets and create and
manage predictive models.  They are similar but not identical APIs.  But they share a
common set of stages:

.. image:: https://d2uakhpezbykml.cloudfront.net/images/PREDIT.jpg
  :width: 50%
  :align: center
  :alt: AutoML PREDIT

- Importing data for training
- Train models with multiple algorithms and hyperparameters
- Evaluate model performance and choose one or more for deployment
- Deploy selected models
- Predict results with new data against deployed models
- Review performance of deployed models

Since ITEDPR is hard to remember we refer to this pipeline by its conveniently mnemonic anagram: "PREDIT" (French for "predict"). The A2ML project provides classes which implement this pipeline for various Cloud AutoML providers
and a command line interface that invokes stages of the pipeline.

