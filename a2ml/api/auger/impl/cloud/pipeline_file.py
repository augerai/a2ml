import os
import urllib.parse
import urllib.request

from .base import AugerBaseApi
from ..exceptions import AugerException


class AugerPipelineFileApi(AugerBaseApi):
    """Auger Pipeline File API."""

    def __init__(self, ctx, experiment_api, pipeline_file_id=None):
        super(AugerPipelineFileApi, self).__init__(
            ctx, experiment_api, None, pipeline_file_id)

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
        if status is None:
            return
        message = {
            'not_requested': 'Starting to buid model for download...',
            'pending': 'Buiding model for download...',
            'success': 'Model is ready for download...'}
        self.ctx.log(message.get(status, status))
