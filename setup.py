import os
import codecs
import sys

from setuptools import setup
from setuptools import find_packages
from setuptools.command.install import install

VERSION = '0.3.5'

# Get the long description from the README file
here = os.path.abspath(os.path.dirname(__file__))
with codecs.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


class VerifyVersionCommand(install):
    """Verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'

    def run(self):
        tag = os.getenv('CIRCLE_TAG', '')

        if not tag.endswith(VERSION, 1):
            info = "Git tag: {0} doesn't match version of a2ml: {1}".format(
                tag, VERSION
            )
            sys.exit(info)

install_requires = [
    'numpy<=1.16.2,>=1.16.0',
    'pyarrow==0.16.0',
    'auger-hub-api-client>=0.6.1',
    'click',
    'shortuuid',
    'docutils<0.16,>=0.10',
    'ruamel.yaml<=0.15.89,>=0.15.35',
    'requests',
    'pandas==0.23.4',
    'smart_open==1.9.0',
    'jsonpickle',
    'feather-format'
]

extras = {
    'testing': [
        'flake8',
        'mock',
        'pytest',
        'pytest-cov',
        'pytest-runner',
        'pytest-xdist',
        'tox',
        'twine',
        'wheel>=0.30.0,<0.31.0'
    ],
    'docs': [
        'sphinx'
    ],
    'server': [
        'celery==4.4.0',
        'aioredis',
        'asyncio',
        'fastapi',
        'gevent',
        'redis',
        'uvicorn',
        's3fs',
        'boto3'
    ],
    'azure': [
        'azureml-sdk[automl]==1.3.0'
    ],
    'google': [
        'google-cloud-automl'
    ]
}

# Meta dependency groups.
all_deps = []
for group_name in extras:
    all_deps += extras[group_name]
extras['all'] = all_deps

description = """A2ML ("Automate AutoML") is a set of scripts to automate
 Automated Machine Learning workflows from multiple vendors."""

setup(
    name='a2ml',
    version=VERSION,
    description=description,
    long_description=description,
    # TODO: Convert readme to rst for azureml / wheels bug
    # long_description=long_description,
    # long_description_content_type='text/markdown',
    author='Auger AI',
    author_email='hello@auger.ai',
    url='https://github.com/augerai/a2ml',
    zip_safe=False,
    platforms='any',
    test_suite='tests',
    python_requires='>=3',
    keywords='augerai aa2ml.cmdl.cmdl:cmdluger ai '
        'machine learning automl deeplearn api sdk',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        "Intended Audience :: System Administrators",
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        "Programming Language :: Python :: 3 :: Only"
    ],
    install_requires=install_requires,
    extras_require=extras,
    tests_require=extras['testing'],
    entry_points={
        'console_scripts': [
            'a2ml=a2ml.cmdl.cmdl:cmdl'
        ]
    },
    cmdclass={
        'verify': VerifyVersionCommand
    },
    packages=find_packages(),
    package_data={
        'a2ml': [
            'api/azure/*.template',
            'cmdl/template/*.template',
            'cmdl/template/*.yaml'
        ]
    }
)
