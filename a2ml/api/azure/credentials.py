import os
import json
from azureml.core.authentication import ServicePrincipalAuthentication

from a2ml.api.utils.base_credentials import BaseCredentials
from .exceptions import AzureException

class Credentials(BaseCredentials):
    """Manage credentials on user computer."""
    def __init__(self, ctx):
        super(Credentials, self).__init__(ctx, "azure")
        self.subscription_id = None
        self.directory_tenant_id = None
        self.application_client_id = None
        self.client_secret = None

    def load(self):
        content = {}

        if hasattr(self.ctx, 'credentials'):
            content = self.ctx.credentials
        elif 'AZURE_CREDENTIALS' in os.environ:
            content = os.environ.get('AZURE_CREDENTIALS', None)
            content = json.loads(content) if content else {}
        else:
            if self._credentials_file_exist():
                with open(self.creds_file, 'r') as file:
                    content = json.loads(file.read())
            else:
                azure_creds_file = os.path.abspath('%s/.azureml/auth/azureProfile.json' % os.environ.get('HOME', ''))
                if os.path.exists(azure_creds_file):
                    from a2ml.api.utils import fsclient
                    try:
                        with fsclient.open_file(azure_creds_file, "r", encoding='utf-8-sig', num_tries=0) as file:
                            res = json.load(file)
                            content = {
                                'subscription_id': res['subscriptions'][0]['id']
                            }
                    except Exception as e:
                        if self.ctx.debug:
                            import traceback
                            traceback.print_exc()

        self.subscription_id = content.get('subscription_id')
        self.directory_tenant_id = content.get('directory_tenant_id')
        self.application_client_id = content.get('application_client_id')
        self.client_secret = content.get('client_secret')

        return self

    def serialize(self):
        return {
            'subscription_id' : self.subscription_id,
            'directory_tenant_id' : self.directory_tenant_id,
            'application_client_id': self.application_client_id,
            'client_secret': self.client_secret
        }

    def get_serviceprincipal_auth(self):        
        svc_pr = None
        if self.client_secret:
            svc_pr = ServicePrincipalAuthentication(
                tenant_id=self.directory_tenant_id,
                service_principal_id=self.application_client_id,
                service_principal_password=self.client_secret
            )

        return svc_pr

    def save(self):
        self._ensure_credentials_file()

        content = self.serialize()
        with open(self.creds_file, 'w') as file:
            file.write(json.dumps(content))

    def verify(self):
        if self.subscription_id is None:
            raise AzureException('Please provide Azure subscription id...')

        return True
