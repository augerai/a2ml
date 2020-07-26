import logging
import pytest
import os

from a2ml.api.utils import fsclient


@pytest.fixture(scope="class")
def config_context(request):
    logging.basicConfig(format='%(asctime)s %(filename)s:%(lineno)s %(levelname)-8s %(funcName)s %(message)s',
                        level=logging.INFO,
                        datefmt='%Y-%m-%d %H:%M:%S')

    creds_envs = fsclient.read_text_file("./develop.client.env")
    for env in creds_envs.splitlines():
        ar_env = env.split("=")
        if ar_env[0] == 'AUGER_CREDENTIALS':
            os.environ['AUGER_CREDENTIALS'] = ar_env[1]

        if ar_env[0] == 'AZURE_CREDENTIALS':
            os.environ['AZURE_CREDENTIALS'] = ar_env[1]

    return
