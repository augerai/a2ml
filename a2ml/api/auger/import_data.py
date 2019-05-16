

class AugerImport(object):
    """Import data into Auger."""
    def __init__(self, ctx):
        super(AugerImport, self).__init__()
        self.ctx = ctx

    def import_data(self):
        self.ctx.log('Not implemented yet.'
            ' You may use data loaded to any public file server'
            ' and provide url to this data file as data service...')
