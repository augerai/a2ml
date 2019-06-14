from setuptools import setup
from setuptools import find_packages

install_requires = [
    'click', 'scikit-learn<=0.20.3,>=0.19.0', 'sklearn', 'wheel==0.30.0',
    'requests', 'requests-toolbelt', 'shortuuid', 'pandas<=0.23.4,>=0.21.0',
    'lightgbm<=2.2.1,>=2.0.11', 'scipy<=1.1.0,>=1.0.0', 'numpy<=1.16.2,>=1.11.0',
    'ruamel.yaml<=0.15.89,>=0.15.35', 'auger-hub-api-client>=0.5.6',
    'azureml', 'azureml.core', 'azureml.train', 'azureml.train.automl',
    'google-cloud-automl']

extras = {
    'testing': ['pytest', 'pytest-cov', 'pytest-xdist', 'flake8', 'mock']
}

# Meta dependency groups.
all_deps = []
for group_name in extras:
    all_deps += extras[group_name]
extras['all'] = all_deps

setup(
    name='a2ml',
    version='0.1',
    description=('The A2ML ("Automate AutoML") project is a set of scripts to automate '
                 'Automated Machine Learning tools from multiple vendors.'),
    author='Deep Learn',
    author_email='augerai@dplrn.com',
    url='https://github.com/deeplearninc/a2ml',
    license='MIT',
    install_requires=install_requires,
    extras_require=extras,
    entry_points={
        'console_scripts': [
            'a2ml=a2ml.cmdl.cmdl:cmdl'
        ]
    },
    packages=find_packages()
)
