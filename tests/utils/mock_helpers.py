class MockHelpers(object):

    class Placeholder(object):
        def __init__(self):
            self.args = None
            self.kwargs = None
            self.times = 0

        def reset(self):
            self.args = None
            self.kwargs = None
            self.times = 0

    @staticmethod
    def raise_(exception):
        raise exception

    @staticmethod
    def pass_method(target, method, monkeypatch):
        def empty_method(*args, **kwargs): pass
        monkeypatch.setattr(target, method, empty_method)

    @staticmethod
    def called_with(target, method, monkeypatch):
        def method_mock(*args, **kwargs):
            placeholder.args = args
            placeholder.kwargs = kwargs
            placeholder.times += 1

        placeholder = MockHelpers.Placeholder()
        monkeypatch.setattr(target, method, method_mock)
        return placeholder

    @staticmethod
    def count_calls(target, method, monkeypatch):
        def method_mock(*args, **kwargs):
            placeholder.times += 1

        placeholder = MockHelpers.Placeholder()
        monkeypatch.setattr(target, method, method_mock)
        return placeholder
