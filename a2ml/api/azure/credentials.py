import os
import json
import shutil
from a2ml.api.utils.base_credentials import BaseCredentials
from .exceptions import AzureException
from a2ml.api.utils import fsclient


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
        if hasattr(self.ctx, 'credentials') and self.ctx.credentials:
            content = self.ctx.credentials
        elif 'AZURE_CREDENTIALS' in os.environ:
            content = os.environ.get('AZURE_CREDENTIALS', None)
            content = json.loads(content) if content else {}
        else:
            #look for service principal credentials
            if self._credentials_file_exist():
                with open(self.creds_file, 'r') as file:
                    content = json.loads(file.read())
            else:
                content = self._load_azure_cred_file()

                if not content.get('subscription_id') and not self.ctx.config.get('use_server'):
                    from azureml.core.authentication import InteractiveLoginAuthentication
                    #fallback to force browser login for token
                    interactive_auth = InteractiveLoginAuthentication(force=True)
                    interactive_auth.get_authentication_header()

                    content = self._load_azure_cred_file()
                                
        self.subscription_id = content.get('subscription_id')
        self.directory_tenant_id = content.get('directory_tenant_id')
        self.application_client_id = content.get('application_client_id')
        self.client_secret = content.get('client_secret')

        return self

    def _load_azure_cred_file(self):
        content = {}

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
        
        return content

    def login(self, username, password, organization, url=None):
        self.load()
        try:
            self.save()
            self.ctx.log(
                'You are now logged in to Azure')
        except Exception as exc:
            exc_text = str(exc)
            self.ctx.log(exc_text)

    def logout(self):
        self.load()
        azure_root_dir = os.path.abspath('%s/.azureml' % os.environ.get('HOME', ''))
        fsclient.remove_folder(azure_root_dir)
        self.subscription_id = None
        self.directory_tenant_id = None
        self.application_client_id = None
        self.client_secret = None
        self.save()
        self.ctx.log('You are logged out of Azure.')

    def whoami(self):
        self.load()
        if self.subscription_id is None:
            self.ctx.log('Please login to Azure...')
        else:
            self.ctx.log(
                'subscription_id: %s directory_tenant_id:%s application_client_id:%s client_secret:%s' % (
                    self.subscription_id,
                    self.directory_tenant_id,
                    self.application_client_id,
                    self.client_secret))

    def serialize(self):
        return {
            'subscription_id' : self.subscription_id,
            'directory_tenant_id' : self.directory_tenant_id,
            'application_client_id': self.application_client_id,
            'client_secret': self.client_secret
        }

    def get_serviceprincipal_auth(self):
        from azureml.core.authentication import ServicePrincipalAuthentication

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
        if self.ctx.config.get('use_server'):
            if not self.subscription_id or \
               not self.directory_tenant_id or \
               not self.application_client_id or \
               not self.client_secret:
               raise AzureException('Please provide azure.json file with Azure AD application and service principal.')

        elif self.subscription_id is None:
            raise AzureException('Please provide your credentials to Azure...')

        return True
