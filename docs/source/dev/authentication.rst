**************
Authentication
**************

Depending on the :doc:`configuration` of A2ML, authentication will be with the A2ML Cloud or directly to providers.

A2ML Cloud
==========

Authenticating with |a2mlcloud| will soon allow you to have one account which manages all provider credentials. All providers can then be run without individual configuration.

CLI Login
---------

You can login to the A2ML Cloud with the ``a2ml auth login`` command.

.. code-block:: bash

  $ a2ml auth login

You will be prompted for your A2ML service user and password. 

Download Credentials
--------------------

A2ML credentials can be downloaded as an ``auger.json`` file from your organization's https://app.auger.ai/<project_name>/**settings**.

.. code-block:: bash

  $ export AUGER_CREDENTIALS=~/auger.json

.. note::

  This would be a JSON string of your credentials.

The ``auger.json`` file can also be referred to by:

  - An environment variable called ``AUGER_CREDENTIALS_PATH``
  - An attribute path_to_credentials inside ``config.yaml``


Individual Providers
====================

.. |a2mlcloud| raw:: html

   <a href="https://app.auger/signup" target="_blank">A2ML Cloud</a>


|a2mlcloud| can manage the usage of Google Cloud AutoML or Azure AutoML for you. If set up on your own you must configure the underlying AutoML service corrrectly to be accessed from the server you are running.


To connect directly to any or all providers configure each individually.

Azure Provider
--------------

CLI Login
^^^^^^^^^
The Azure AutoML service allows browser login. Run any ``a2ml`` command and a login URL will open in the default browser.

To explicitly login to azure run.

.. code-block:: bash

  $ a2ml auth login -p azure

JSON File
^^^^^^^^^
.. |spc| raw:: html

  <a href="https://docs.microsoft.com/en-us/azure/active-directory/develop/howto-create-service-principal-portal" target="_blank">service principal credentials</a>

To login programmatically without the browser use the |spc|.

.. note::

  Follow the above directions to create an azure.json file with values specific to your account.

.. code-block:: JSON
  :caption: azure.json
  :name: azure.json

  {
    "subscription_id":"",
    "directory_tenant_id":"",
    "application_client_id":"",
    "client_secret":""
  }


.. code-block:: bash

  $ export AZURE_CREDENTIALS=~/azure.json

.. note::

  This would be a JSON string of your azure credentials.

The azure.json file can also be referred to by:

  - An environment variable called ``AZURE_CREDENTIALS_PATH``
  - An attribute path_to_credentials inside ``config.yaml``

Google Cloud Provider
---------------------
If you haven't run Google Cloud AutoML, set up a service account and save the credentials to a JSON file which you store in your project directory.  Then set up the ``GOOGLE_APPLICATION CREDENTIALS`` environment variable to point to the saved file.  For example:

.. code-block:: bash

  $ export GOOGLE_APPLICATION_CREDENTIALS="/Users/user/a2ml/automl.json"


For ease of use you can set up a default project ID to use with your project with the ``PROJECT_ID`` environment variable. For example:  

.. code-block:: bash

  $ export PROJECT_ID="automl-test-237311"


Detailed instructions for setting up |gcautoml|.

.. |gcautoml| raw:: html

   <a href="https://cloud.google.com/vision/automl/docs/before-you-begin" target="_blank">Google Cloud AutoML</a>

.. _Auth_Matrix:

A2ML Authentication Matrix
-------------------------------
The following shows which authentication components are necessary depending on your A2ML use case.

.. csv-table:: Authentication Matrix
   :file: authentication_matrix.csv
