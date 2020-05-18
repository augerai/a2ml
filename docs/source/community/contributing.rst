************
Contributing
************

.. |contribute| raw:: html

   <a href="https://github.com/augerai/a2ml/blob/master/CONTRIBUTING.md" target="_blank">A2ML project</a>

Learn how to get involved in the |contribute|.

Documentation
=============

.. |sphinx| raw:: html

   <a href="https://www.sphinx-doc.org/en/master/usage/quickstart.html" target="_blank">sphinx</a>

Documents are generated using |sphinx|. To generate new docs locally you will want to navigate to the /docs directory located in the root of this project.

There is currently an index.rst file which is the entry point. This file loads all other document files.

There are currently two top level directories with documentation.

    - /dev
    - /community


.. |rst| raw:: html

   <a href="https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html" target="_blank">restructured text</a>

To edit the files in there directly using |rst| syntax or you can add files for new sections.  Any new sections will need to have the path added in index.rst file.

Building Documentation
----------------------

First, install documentation-related dependencies:

.. code-block:: bash

    $ make develop-docs

Then, from inside the /docs directory run:

.. code-block:: bash

    $ make html

This will create new files inside of the /build directory.  If you notice that your changes aren't showing up try deleting all the contents inside build/ and running make html to force rebuild.

Viewing Documentation in the Browser
------------------------------------

.. code-block:: bash

    open ./build/html/index.html


Implementing A2ML for Another AutoML Provider
==============================================
The A2ML Model class in A2ML.PY abstracts out the PREDIT (ITEDPR) pipeline.  

Implementations are provided for

 - **Auger.AI (Auger)**
 - **Azure AutoML (AZModel)**
 - **Google Cloud AutoML Tables (GCModel)**
 
 If you want to add support for another AutoML provider of your choice, implement a child class of Model as shown below (replacing each "pass" with your own code.

.. code-block:: python

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