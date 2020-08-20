# -*- coding: utf-8 -*-
import os
import argparse

from auger_ml.model_exporter import ModelExporter

# path to predict is path to csv file with headers to get predictions
def get_predictions(path_to_predict=None, threshold=None, model_path=None):
    #features is an array mapping your data to the feature, your feature and data should be
    #the same that you trained your model with.
    #If it is None, features read from model/options.json file
    #['feature1', 'feature2']
    features = None 

    # data is an array of arrays to get predictions for, input your data below
    # each record should contain values for each feature
    records = [[],[]]

    if path_to_predict:
        path_to_predict=os.path.abspath(path_to_predict)
            
    predictions = ModelExporter({}).predict_by_model(
        records=records,
        model_path=model_path,
        path_to_predict=path_to_predict,
        features=features,
        threshold=threshold
    )

    if path_to_predict:
        print("CSV file with prediction created: %s"%predictions)

    else:
        # you may convert pandas dataframe to list with index:
        #predictions = predictions.reset_index().iloc[:, list((0, -1))]
        #predictions = predictions.values.tolist()
        #if threshold specified append probabilities to end
        predictions_no_proba = predictions[predictions.columns.drop(
            list(predictions.filter(regex='proba_')))]
        predictions_proba = predictions.filter(regex='proba_').reset_index()
        predictions = predictions_no_proba.reset_index().iloc[:, list((0, -1))]

        if not predictions_proba.empty:
            predictions = pd.merge(predictions, predictions_proba, on='index')
            #print(predictions)

    return predictions

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--path_to_predict", help="Path to file for predict", type=str, default=None)
    parser.add_argument("--threshold", help="Threshold to use for predict_proba", type=float, default=None)
    parser.add_argument("--model_path", help="Path to folder with model", type=str, default='./exported_model/model')
    args = parser.parse_args()

    get_predictions(path_to_predict=args.path_to_predict, threshold=args.threshold, model_path=args.model_path)
