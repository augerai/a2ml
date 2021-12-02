import os
import codecs
import sys

from setuptools import setup
from setuptools.command.install import install

from a2ml import __version__

# Get the long description from the README file
here = os.path.abspath(os.path.dirname(__file__))
with codecs.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


class VerifyVersionCommand(install):
    """Verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'

    def run(self):
        tag = os.getenv('CIRCLE_TAG', '')

        if not tag.endswith(__version__, 1):
            info = "Git tag: {0} doesn't match version of a2ml: {1}".format(
                tag, __version__
            )
            sys.exit(info)


install_requires = [
    'numpy==1.19.2',
    'pandas==1.2.4',
    'joblib==1.0.1',
    'ruamel.yaml',
    'pyarrow==1.0.1',
    'scipy==1.5.2',
    'asyncio',
    'boto3',
    'auger-hub-api-client==0.7.4',
    'click<8.0,>=7.0', #celery 5
    'shortuuid',
    'docutils<0.16,>=0.10',
    'psutil',
    'requests',
    'smart_open==5.1.0',
    'jsonpickle',
    'websockets',
    'liac-arff==2.4.0',
    'xlrd==1.2.0'
]

extras = {
    'testing': [
        'flake8<=3.7.9,>=3.1.0',  # version for azure
        'mock',
        'pytest',
        'pytest-cov',
        'pytest-runner',
        'pytest-xdist',
        'twine',
        'vcrpy',
        'wheel>=0.30.0,<0.31.0'
    ],
    'docs': [
        'sphinx'
    ],
    'server': [
        'aioredis',
        'celery==4.4.0',
        'fastapi',
        'gevent',
        'redis',
        's3fs>=0.4.0,<0.5.0',
        'uvicorn',
        'scikit-learn==0.24.2'
    ],
    'azure': [
        #'scikit-learn~=0.22.2',
        #'xgboost<=0.90',
        # https://github.com/Azure/azure-sdk-for-python/issues/13871
        #'azure-mgmt-resource==10.2.0',
        #this needs to move to setup.azure.py and do not include default
        'azureml-sdk[automl]==1.29.0'
    ],
    'google': [
        'google-cloud-automl'
    ],
    'predict': [
        'auger.ai.predict==1.0.90'
    ]
}

# Meta dependency groups.
all_deps = []
for group_name in extras:
    if group_name != 'predict' and group_name != 'google' and group_name != 'azure':
        all_deps += extras[group_name]

extras['all'] = all_deps


setup(
    install_requires=install_requires,
    extras_require=extras,
    tests_require=extras['testing'],
    cmdclass={
        'verify': VerifyVersionCommand
    }
)
