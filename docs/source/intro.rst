
A2ML - Automation of AutoML
---------------------------
.. |augerai| raw:: html

   <a href="https://auger.ai" target="_blank">Auger.AI</a>

.. |augerairepo| raw:: html

  <a href="http://github.com/augerai/a2ml" target="_blank">open source</a>

The A2ML ("Automate AutoML") project is a Python API and set of command line tools to **automate Automated Machine Learning** tools from multiple vendors. 

A2ML provides a common API for all cloud-oriented AutoML vendors. 
Today that is Microsoft Azure AutoML, Google Cloud AutoML, and Auger AutoML. 
All of A2ML is |augerairepo| and free in perpetuity. 
Other AutoML providers can be added as the fundamental stages apply to all them.  

Performing all phases of the model building, training and usage process with those other cloud vendors' products is hundreds of lines of code.
A short perusal of the source in this repo can validate that.  Also using your the A2ML API 
in your apps that need predictive models removes vendor lockin to each particular cloud providers' API.

Google and Microsoft do not provide ongoing review and monitoring of deployed model accuracy
with their cloud AutoML APIs.  A2ML adds a model review capability for those providers.  

With A2ML, data scientists and developers can now train their datasets against multiple AutoML providers 
to get the best possible predictive model. 


The PREDIT Pipeline
===================
Every AutoML vendor has their own API to manage the datasets and create and
manage predictive models.  They are similar but not identical APIs.  But they share a
common set of stages:

.. image:: https://d2uakhpezbykml.cloudfront.net/images/PREDIT.jpg
  :width: 50%
  :align: center
  :alt: AutoML PREDIT

- \ **I**\mporting data for training

- \ **T**\rain models with multiple algorithms and hyperparameters

- \ **E**\valuate model performance and choose one or more for deployment

- \ **D**\eploy selected models

- \ **P**\redict results with new data against deployed models

- \ **R**\eview performance of deployed models

Since ITEDPR is hard to remember we refer to this pipeline by its conveniently mnemonic anagram: "PREDIT" (French for "predict"). The A2ML project provides classes which implement this pipeline for various Cloud AutoML providers
and a command line interface that invokes stages of the pipeline.

