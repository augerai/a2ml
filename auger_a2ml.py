import time

from auger_cli.config import AugerConfig
from auger_cli.client import AugerClient

from auger_cli.api import auth
from auger_cli.api import experiments


def run_iris_train():
    # To read login information from experiment dir:
    #config_settings={'login_config_path': "./iris_train"}

    # To use root user dir to read login information
    config_settings={}

    # Read experiment setting from iris_train\auger_experiment.yml 
    client = AugerClient(AugerConfig(config_dir="./iris_train", 
        config_settings=config_settings))

    # To login to Auger:
    # url is optional parameter, hub_url may be specified in config_settings
    auth.login(client, "adam@auger.ai", "ProfPlum1")

    # Experiment run, after finish, save experiment session parameters to .auger_experiment_session.yml
    experiments.run(client)

    while True:
        leaderboard, info = experiments.read_leaderboard(client)

        print(info.get("Status"))
        if info.get("Status") == 'error':
            raise Exception("Iris dataset train failed: %s"%info.get("Error"))

        if info.get("Status") != 'completed':
            time.sleep(5)
            continue

        break

    # Create pipeline based on best trial    
    pipeline_id = experiments.export_model(client, trial_id=leaderboard[0]['id'], deploy=True)

    # Pipeline can be reused multiple time, predict can be called without cluster run
    result = experiments.predict_by_file(client, pipeline_id=pipeline_id, file='./iris_train/files/iris_data_test.csv', save_to_file=False)
    print(result[0])

    result = experiments.predict_by_file(client, pipeline_id=pipeline_id, file='./iris_train/files/iris_data_test.csv', save_to_file=False)
    print(result[0])

run_iris_train()