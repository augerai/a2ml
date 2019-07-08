import types

class ErrorHandler(type):
   def __new__(cls, name, bases, attrs):
      for attr_name, attr_value in attrs.items():
         if isinstance(attr_value, types.FunctionType):
            attrs[attr_name] = cls._error_handler(attr_value)
      return super(ErrorHandler, cls).__new__(cls, name, bases, attrs)

   @classmethod
   def _error_handler(cls, decorated):
      def wrapper(self, *args, **kwargs):
        try:
            return decorated(self, *args, **kwargs)
        except Exception as exc:
            if self.ctx.debug:
                import traceback
                traceback.print_exc()
            self.ctx.log(str(exc))
      return wrapper
