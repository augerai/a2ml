from functools import wraps

def show_result(decorated):
    @wraps(decorated)
    def wrapper(self, *args, **kwargs):
        showresult = self.ctx.config.get('showresult', False)
        result = decorated(self, *args, **kwargs)
        if showresult:
            self.ctx.log(result)
        # else:
        # 	for provider, res in result.items():
        # 		if "result" in res and not res["result"]:
        # 			self.ctx.log("Provider '%s' return error: %s"%(provider, res.get("data")))		

        return result
    return wrapper
