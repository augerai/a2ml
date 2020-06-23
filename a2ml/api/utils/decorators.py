def error_handler(decorated):
    def wrapper(self, *args, **kwargs):
        try:
            return decorated(self, *args, **kwargs)
        except Exception as exc:
            if self.ctx.debug:
                import traceback
                traceback.print_exc()

            if "ServiceException" in str(type(exc)):
                exc = Exception(exc.message)
                
            self.ctx.log(str(exc))
            if not hasattr(self.ctx, 'not_reraise_exceptions')\
               or not self.ctx.not_reraise_exceptions:
                raise exc
                
    return wrapper


def authenticated(decorated):
    def wrapper(self, *args, **kwargs):
        self.credentials.verify()
        return decorated(self, *args, **kwargs)
    return wrapper
