import argparse 
import os
import a2ml
import gc_a2ml

def main():

    parser = argparse.ArgumentParser(prog='GC_A2ML',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''A2ML - Automating AutoML. 
    
    Uppercase P-R-E-D-I-T options run parts of the pipeline. They generally
    correspond to Model methods.  
    
    Lowercase options set project, dataset, model and others that span pipeline stages
    (geneerally correspond to Model instance variables).''',
        epilog='''A typical usage of the PREDICT pipeline would be successive invocations with the following options:
        -- IMPORT
        -- TRAIN
        -- EVALUATE
        -- DEPLOY
        -- PREDICT
        -- REVIEW''')
           
    # capital letter arguments are pipeline phases
    parser.add_argument('-P','--PREDICT',help='Predict with deployed model',action='store_true')
    parser.add_argument('-R','--REVIEW',help='Review specified model info',action='store_true')
    parser.add_argument('-E','--EVALUATE',help='Evaluate models after training',action='store_true')
    parser.add_argument('-D','--DEPLOY',help='Deploy model',action='store_true')
    parser.add_argument('-I','--IMPORT',help='Import data for training',action='store_true')
    parser.add_argument('-C','--CONFIGURE',help='Configure model options before training',action='store_true')
    parser.add_argument('-T','--TRAIN',help='Train the model',action='store_true')
    # lower case letter arguments apply to multiple phases
    parser.add_argument('-p','--project',help='Google Cloud project ID, overrides PROJECT_ID env var')
    parser.add_argument('-d','--dataset',help='Google Cloud dataset ID')
    parser.add_argument('-n','--name',help='Model name')
    parser.add_argument('-i','--model_id',help='Model ID')
    parser.add_argument('-s','--source',help='Source path for loading dataset')
    parser.add_argument('-t','--target',help='Target column from dataset')
    parser.add_argument('-b','--budget',type=int, help='Max training time in seconds')
    parser.add_argument('-x','--exclude',help='Excludes given columns from model')
    parser.add_argument('-z','--score_threshold',help='Score threshold for prediction')
    parser.add_argument('-r','--region',help='Compute region (Google Cloud beta must=us-central1')
    parser.add_argument('-m','--metric',help='Metric to evaluate quality of model')
    parser.add_argument('-a','--automl',help='AutoML provider')

    args = parser.parse_args()
    print("Parsed args: {}".format(args))
    name = args.name

    if (args.project is not None):
        project_id = args.project
    else:  # default project read from environment
        project_id = os.getenv('PROJECT_ID')
    if (args.region is not None):
        region = args.region
    else:
        region = 'us-central1'

    if ((args.automl == "GC") or (args.automl is None)):
        print("Creating Google Cloud AutoML client")
        model = GCModel(project_id,region)
    elif (args.automl == "Auger"):
        print("Creating Auger.AI client")
        model = a2ml.api.a2ml.AugerModel()
    if (args.project is not None):
        project_id = args.project
    else:  # default project read from environment
        project_id = os.getenv('PROJECT_ID')

    if (args.dataset is not None):
        model.dataset_id = args.dataset 
    if (args.target is not None):
        target = args.target

    if (args.source is not None):
        source = args.source 
    if (args.budget is not None):
        training_budget = args.budget
    else:
        training_budget = 3600
    if (args.metric is not None):
        metric = args.metric
    if (args.model_id):
        model.id = args.model_id
    if (args.score_threshold is not None):
        score_threshold = args.score_threshold
    else: 
        score_threshold = 0.0
    if (args.exclude is not None):
        excluded = args.exclude.split(',')
    
    if (args.IMPORT): 
        model.import_data(source,name)
    if (args.TRAIN):
        model.train(target,excluded,training_budget,metric)

    if (args.EVALUATE):
        model.evaluate()
    if (args.DEPLOY):
        model.deploy()
    if (args.PREDICT):
        model.predict(source,score_threshold)
    if (args.REVIEW):
        model.review()

if __name__ == '__main__':
    main()