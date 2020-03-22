def show_result(decorated):
    def wrapper(self, *args, **kwargs):
        showresult = self.ctx.config.get('showresult', False)
        result = decorated(self, *args, **kwargs)
        if showresult:
            self.ctx.log(result)
        return result
    return wrapper
