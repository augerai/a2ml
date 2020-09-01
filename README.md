# a2ml - Automation of AutoML

[![CircleCI](https://img.shields.io/circleci/build/gh/augerai/a2ml/master)](https://circleci.com/gh/augerai/a2ml)
[![Join the chat](https://img.shields.io/gitter/room/augerai/a2ml.svg)](https://gitter.im/augerai/a2ml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://raw.githubusercontent.com/augerai/a2ml/master/LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/a2ml.svg)](https://pypi.org/project/a2ml/)
[![PyPI - A2ML Versions](https://img.shields.io/pypi/v/a2ml.svg)](https://pypi.org/project/a2ml/)


The A2ML ("Automate AutoML") project is a Python API and set of command line tools to automate Automated Machine Learning tools from multiple vendors. The intention is to provide a common API for all Cloud-oriented AutoML vendors.  Data scientists can then train their datasets against multiple AutoML models to get the best possible predictive model.  May the best "algorithm/hyperparameter search" win.  Full documentation for A2ML is available at [a2ml.org](http://a2ml.org)

## The PREDIT Pipeline
Every AutoML vendor has their own API to manage the datasets and create and
manage predictive models.  They are similar but not identical APIs.  But they share a
common set of stages:
* Importing data for training
* Train models with multiple algorithms and hyperparameters
* Evaluate model performance and choose one or more for deployment
* Deploy selected models
* Predict results with new data against deployed models
* Review performance of deployed models

Since ITEDPR is hard to remember we refer to this pipeline by its conveniently mnemonic anagram: "PREDIT" (French for "predict"). The A2ML project provides classes which implement this pipeline for various Cloud AutoML providers
and a command line interface that invokes stages of the pipeline.

## Setup
A2ML is distributed as a python package, so to install it:

```sh
$ pip install -U a2ml
```

It will install Auger provider.

To use Azure AutoML:

### Mac:
```sh
$ brew install libomp
```
#### For Mac OS High Sierra and below:
```sh
$ SKLEARN_NO_OPENMP=1 pip install "scikit-learn==0.21.3"
$ pip install "a2ml[azure]" --ignore-installed onnxruntime onnx nimbusml
```

### Linux:
```sh
$ apt-get update && apt-get -y install gcc g++ libgomp1
```

```sh
$ pip install "a2ml[azure]"
```

To use Google Cloud:

```sh
$ pip install "a2ml[google]"
```

To install everything including testing and server code:

```sh
$ pip install "a2ml[all]"
```

## Development
To release a new version the flow should be:
1. Change the `__version__` variable in `a2ml/__init__.py` to match what you want to release, minus the "v". By default it would be "<current-milestone>.dev0", for example "0.3.0.dev0". This ensures we don’t accidentally release a dev version to pypi.org. So for when we’re ready to release 0.3.0, the   `__version__` variable should simply be "0.3.0".

2. Commit and push the changes above.

```sh
git tag v<the-version> (for example: git tag v0.3.0)
git push --tags
```

3. verify circleci build passed and docker image tag exists:

```sh
pip install -U a2ml==0.3.0
docker pull augerai/a2ml:v0.3.0
```

4. Increment the `__version__` variable in `a2ml/__init__.py` to the next version in the current milestone. For example, "0.3.1.dev0"
