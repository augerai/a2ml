import os
import json
import time
import requests
from requests_toolbelt import MultipartEncoder

from a2ml.api.auger.hub.hub_api import HubApi
from a2ml.api.auger.hub.org import AugerOrgApi
from a2ml.api.auger.hub.project import AugerProjectApi
from a2ml.api.auger.hub.cluster import AugerClusterApi
from a2ml.api.auger.hub.hub_api import STATE_POLL_INTERVAL

from a2ml.api.auger.credentials import Credentials

class AugerImport(object):
    """Import data into Auger."""
    def __init__(self, ctx):
        super(AugerImport, self).__init__()
        self.ctx = ctx
        self.credentials = Credentials(ctx.config['auger']).load()

    def import_data(self):
        try:
            file_to_upload = self.ctx.config['config'].get('data/source', None)
            if file_to_upload is None:
                raise Exception(
                    'Please specify in config.yaml file to import to Auger...')
            file_to_upload = os.path.abspath(
                os.path.join(os.getcwd(), file_to_upload))
            if not os.path.isfile(file_to_upload):
                raise Exception(
                    'Can\'t find file to import: %s' % file_to_upload)

            self.ctx.log('Importing to Auger file %s' % file_to_upload)

            if self.credentials.token is None:
                raise Exception(
                    'Please provide your credentials to import data to Auger...')

            org_name = self.ctx.config['auger'].get('org_name', None)
            if org_name is None:
                raise Exception(
                    'Please specify your organization (org_name:) in auger.yaml...')

            project_name = self.ctx.config['auger'].get('project_name', None)
            if project_name is None:
                raise Exception(
                    'Please specify your project (project_name:) in auger.yaml...')

            hub_client = HubApi(
                self.credentials.api_url, self.credentials.token,
                self.ctx.log, self.ctx.config['auger'])

            org = AugerOrgApi(hub_client, org_name).properties()
            if org is None:
                raise Exception('Can\'t find organization %s' % org_name)
            org_id = org.get('id')

            project_api = AugerProjectApi(hub_client, project_name, org_id)
            project = project_api.properties()
            if project is None:
                self.ctx.log('Can\'t find project %s on the Auger Hub.'
                    ' Creating...' % project_name)
                project = project_api.create()
            project_id = project.get('id')
            cluster_id = project.get('cluster_id')

            cluster_api = AugerClusterApi(hub_client, cluster_id)
            if not cluster_api.is_running():
                cluster_api.create(org_id, project_id)
                # huck; for some reason file_uploader_service
                # isn't filled right after cluster is created
                time.sleep(STATE_POLL_INTERVAL)
            cluster = cluster_api.properties()

            print(cluster.get('id'))
            print(cluster.get('status'))
            file_uploader_service = cluster.get('file_uploader_service')
            print(json.dumps(file_uploader_service, indent = 2))
            upload_token = file_uploader_service.get('params').get('auger_token')
            upload_url = '%s?auger_token=%s' % (file_uploader_service.get('url'), upload_token)
            print(upload_url)
            print(upload_token)
            print(self.credentials.username)

            ret = self.uploadFile(file_to_upload, upload_url)
            print(str(ret))
            # print(json.dumps(ret, indent = 2))

        except Exception as exc:
            self.ctx.log(str(exc))

    def uploadFile(self, file_name, url):
        try:
            basename = os.path.basename(file_name)
            m = MultipartEncoder(fields={
                'file':(basename, open(file_name, 'rb'), "application/octet-stream")})
            print(2)
            r = requests.post(url, data=m, headers={'Content-Type': m.content_type})
            return r
        except Exception as e:
            return {"error": e, "error_code": 503}
