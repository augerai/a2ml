************
Installation
************

A2ML is distributed as a python package. To install the client with default AugerAI AutoML provider.

.. code-block:: bash

  $ pip install -U a2ml


Provider Groups
===============

Azure AutoML Provider
---------------------

To include the Azure AutoML provider.

.. code-block:: bash

  $ pip install "a2ml[azure]"

.. |lightgbm| raw:: html

   <a href="https://lightgbm.readthedocs.io/en/latest/Installation-Guide.html" target="_blank">LightGBM</a>

.. warning::

  Azure requires that |lightgbm| be installed.

  .. code-block:: bash

    $ brew install lightgbm



To run Azure AutoML models locally.

.. note:: 
  This will install scikit-learn and several additional dependencies.

.. code-block:: bash

  $ pip install "a2ml[azure]"


Google Cloud Provider
---------------------

To include the Google Cloud AutoML provider.

.. code-block:: bash

  $ pip install "a2ml[google]"

Server Installation
===================

To install server dependencies.

.. code-block:: bash

  $ pip install "a2ml[server]"


Install Everything
==================

To install all providers and server dependencies.

.. code-block:: bash

  $ pip install "a2ml[all]"
