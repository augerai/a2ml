import logging
import pytest
import os


@pytest.fixture(scope="class")
def config_context(request):
    logging.basicConfig(format='%(asctime)s %(filename)s:%(lineno)s %(levelname)-8s %(funcName)s %(message)s',
                        level=logging.INFO,
                        datefmt='%Y-%m-%d %H:%M:%S')

    #os.environ["TEST_CALL_CELERY_TASKS"] = "True"
    # os.environ["HUB_APP_URL"] = 'https://app-staging.auger.ai'
    # os.environ["AUGER_PROJECT_API_TOKEN"] = 'XXX'

    # os.environ["A2ML_PROJECT_PATH"] = os.path.abspath('./tests/fixtures')
    # #os.environ["A2ML_PROJECT_PATH"] = 's3://auger-demo-datasets/a2ml_app'
    # os.environ["AUGER_ORGANIZATION"] = 'mt-org'

    return
