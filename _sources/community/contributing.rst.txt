**************
Contributing
**************

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