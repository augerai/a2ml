from setuptools import setup
from setuptools import find_packages

install_requires = [
    'click','dill','google-cloud-automl','lightgbm','numpy','pandas',
    'sklearn','wheel', 'requests', 'requests-toolbelt', 'shortuuid',
    'auger-hub-api-client>=0.5.6'
]

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
    description=('Th A2ML ("Automate AutoML") project is a set of scripts to automate '
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
