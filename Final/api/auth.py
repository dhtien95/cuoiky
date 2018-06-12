from __future__ import print_function
from oauth2client import file,client,tools

class Auth:
    def __init__(self,SCOPES,store):
        self.SCOPES = SCOPES
        self.store = store
    def getCrendentials(self):
        creds = self.store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('client_secret.json',self.SCOPES)
            creds =tools.run_flow(flow,self.store)

        return  creds