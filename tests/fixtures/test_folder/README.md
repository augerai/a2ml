# Getting Started

1) Install and run Docker service on the computer
2) Pull latest image:
docker pull deeplearninc/auger-ml-worker:stable

3) Run with csv file to use for predictions. Run in command line:

docker run -v ${PWD}:/var/src/auger-ml-worker/exported_model -v <'path to folder with files'>:/var/src/auger-ml-worker/model_data deeplearninc/auger-ml-worker:stable python ./exported_model/client.py --path_to_predict=./model_data/<'file to predict'>

Notes:
  - This command will create file with _predicted postfix in the same folder

4) Run with sample data:
  - edit client.py to fill records variable
  - if order of features are different from originalFeatureColumns in model/options.json: specify features variable
  - Run in command line:

docker run -v ${PWD}:/var/src/auger-ml-worker/exported_model deeplearninc/auger-ml-worker:stable python ./exported_model/client.py
