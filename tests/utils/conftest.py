import logging
import pytest
import os


# def quiet_py4j():
#     """ turn down spark logging for the test context """
#     logger = logging.getLogger('py4j')
#     logger.setLevel(logging.INFO)

#     logging.basicConfig(
#         format="%(asctime)s %(levelname)-8s %(message)s",
#         level=logging.INFO)


@pytest.fixture(scope="class")
def config_context(request):
    #quiet_py4j()
    logging.basicConfig(format='%(asctime)s %(filename)s:%(lineno)s %(levelname)-8s %(funcName)s %(message)s',
                        level=logging.INFO,
                        datefmt='%Y-%m-%d %H:%M:%S')
    
    # os.environ["AUGER_PROJECT_API_TOKEN"] = 'TEST'
    # os.environ["HUB_APP_URL"] = 'https://app-staging.auger.ai'

    return
