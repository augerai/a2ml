import os
import codecs

from setuptools import setup
from setuptools import find_packages
from setuptools.command.install import install

VERSION = '0.1.1'

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
            info = "Git tag: {0} does not match the version of auger-cli: {1}".format(
                tag, VERSION
            )
            sys.exit(info)

install_requires = [
    'click','scikit-learn>=0.19.0','wheel==0.30.0',
    'requests','requests-toolbelt','shortuuid','ruamel.yaml<=0.15.89,>=0.15.35',
    'pandas<=0.23.4,>=0.21.0','auger-hub-api-client>=0.6.1', 'auger.ai'
]

extras = {
    'testing': ['pytest', 'pytest-cov', 'pytest-xdist', 'flake8', 'mock'],
    'azure': ['lightgbm<=2.2.1,>=2.0.11','scipy<=1.1.0,>=1.0.0',
        'numpy<=1.16.2,>=1.11.0','azureml','azureml.core','azureml.train',
        'azureml.train.automl'],
    'google': ['google-cloud-automl']
}

# Meta dependency groups.
all_deps = []
for group_name in extras:
    all_deps += extras[group_name]
extras['all'] = all_deps

setup(
    name='a2ml',
    version='0.1',
    description=('The A2ML ("Automate AutoML") project is a set of scripts to '
                 'automate Automated Machine Learning tools from multiple vendors.'),
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Deep Learn',
    author_email='augerai@dplrn.com',
    url='https://github.com/deeplearninc/a2ml',
    license='MIT',
    zip_safe=False,
    platforms='any',
    test_suite='tests',
    python_requires='>=3',
    keywords='augerai aa2ml.cmdl.cmdl:cmdluger ai machine learning automl deeplearn api sdk',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        "Intended Audience :: System Administrators",
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        "Programming Language :: Python :: 3 :: Only"
    ],
    install_requires=install_requires,
    extras_require=extras,
    entry_points={
        'console_scripts': [
            'a2ml=a2ml.cmdl.cmdl:cmdl'
        ]
    },
    cmdclass={
        'verify': VerifyVersionCommand
    },
    packages=find_packages()
)
