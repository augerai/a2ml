import argparse 
import os
import csv
from google.cloud import automl_v1beta1 as automl
from google.cloud.automl_v1beta1 import enums
# if using A2ML with Google Cloud AutoML tables then
# insure that your GOOGLE_APPLICATION_CREDENTIALS environment variable 
# points to the application credentials file given from your Google Cloud SDK
# you can also set a default PROJECT_ID for Google Cloud in your environment
import abc
from abc import ABC, abstractmethod 
class Model:
    def predict(self):
        pass
    def review(self):
        pass
    def evaluate(self):
        pass
    def deploy(self):
        pass
    def import_data(self,source):
        pass
    def train(self):
        pass

# TODO: implement these for Auger
class AugerModel(Model):  
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

