import os
import urllib.parse
import urllib.request

from a2ml.api.auger.hub.base import AugerBaseApi
from a2ml.api.auger.hub.prediction import AugerPredictionApi
from a2ml.api.auger.hub.utils.exception import AugerException


class AugerPipelineFileApi(AugerBaseApi):
    """Wrapper around HubApi for Auger Pipeline."""

    def __init__(
        self, experiment_api, pipeline_file_id=None):
        super(AugerPipelineFileApi, self).__init__(
            experiment_api, None, pipeline_file_id)

    def create(self, trial_id):
        return self._call_create({'trial_id': trial_id},
            ['not_requested', 'pending'])

    def download(self, url, path_to_download, trial_id):
        if self.object_id is None:
            raise AugerException('Please provide Auger Pipeline File id')

        if not os.path.exists(path_to_download):
            os.makedirs(path_to_download)
        basename = os.path.basename(
            urllib.parse.urlparse(url).path).replace('export_','model-')
        file_name = os.path.join(path_to_download, basename)
        urllib.request.urlretrieve(url, file_name)

        return file_name

    def _get_status_name(self):
        return 's3_model_path_status'

    def _log_status(self, status):
        if self.hub_client.ctx is None:
            return
        message = {
            'not_requested': 'Starting to buid model for download...',
            'pending': 'Buiding model for download...',
            'success': 'Model is ready for download...'}
        self.hub_client.ctx.log(message.get(status, ''))
