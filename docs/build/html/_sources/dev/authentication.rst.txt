**************
Authentication
**************

Authentication with A2ML involves two parts. 

 #. There is authentication between your client (whether it's the `a2ml` cli or the `a2ml` python API) and the service endpoint (either self-hosted or with Auger.AI). 
 #. There is authentication between the service endpoint and each provider. Note that in the case where you run A2ML locally, endpoint authentication is handled automatically. 
    The :ref:`Auth_Matrix` at the end of this section shows this in more detail.

Auger.AI Provider
----------------------------
You can login to the Auger.AI endpoint and provider with the `a2ml auth login` command.

.. code-block:: bash

  $ a2ml auth login

You will be prompted for your Auger service user and password. You can also download your Auger credentials as a credentials.json file and refer to it with an AUGER_CREDENTIALS environment variable.

.. code-block:: bash

  $ export AUGER_CREDENTIALS=~/auger_credentials.json

You can also put the path to credentials.json in an environment variable called AUGER_CREDENTIALS_PATH OR a key inside AUGER.YAML.  

.. note::

  The Auger service can manage your usage of Google Cloud AutoML or Azure AutoML for you. If you choose to set up your own endpoints, you must configure the underlying AutoML service corrrectly to be accessed from the server you are running from.  Here are abbreviated directions for that step for Google, Azure and Auger.

Google Cloud Provider
---------------------
If you haven't run Google Cloud AutoML, set up a service account and save the credentials to a JSON file which you store in your project directory.  Then set up the GOOGLE_APPLICATION CREDENTIALS environment variable to point to the saved file.  For example:

.. code-block:: bash

  $ export GOOGLE_APPLICATION_CREDENTIALS="/Users/adamblum/a2ml/automl.json"


For ease of use you can set up a default project ID to use with your project with the PROJECT_ID environment variable. For example:  

.. code-block:: bash

  $ export PROJECT_ID="automl-test-237311"


Detailed instructions for setting up |gcautoml|

.. |gcautoml| raw:: html

   <a href="https://cloud.google.com/vision/automl/docs/before-you-begin" target="_blank">Google Cloud AutoML</a>

Azure Provider
--------------
The Azure AutoML service allows credentials to be downloaded as a JSON file (such as a config.json file).  This should then be placed in a .azureml subdirectory of your project directory.  Be sure to include this file in your .gitignore:

.. code-block:: bash

  $ **/.azureml/config.json

The Azure subscription ID can be set with the AZURE_SUBSCRIPTION_ID environment variable as in the following example.

.. code-block:: bash

  $ export AZURE_SUBSCRIPTION_ID="d1b17dd2-ba8a-4492-9b5b-10c6418420ce"


.. _Auth_Matrix:

A2ML Authentication Matrix
-------------------------------
The following shows which authentication components are necessary depending on your A2ML use case.

.. csv-table:: Authentication Matrix
   :file: authentication_matrix.csv