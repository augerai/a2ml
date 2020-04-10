**************
Installation
**************

A2ML is distributed as a python package.

.. code-block:: bash

  $ pip install -U a2ml


A2ML also defines feature groups that can be used to install A2ML and the dependencies for a given feature.

To run Azure AutoML:

.. code-block:: bash

  $ pip install "a2ml[azure]"


To run Azure AutoML models locally (this will install scikit-learn and several additional dependencies):

.. code-block:: bash

  $ pip install "a2ml[azure-local]"


For Google Cloud:

.. code-block:: bash

  $ pip install "a2ml[google]"


For everything:

.. code-block:: bash

  $ pip install "a2ml[all]"
