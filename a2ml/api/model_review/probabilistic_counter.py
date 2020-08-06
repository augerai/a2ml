class ProbabilisticCounter(object):
    def __init__(self):
        self._set = set()

    # returns: True - value is new, False, value already included
    def add(self, value):
        hash = value.__hash__()
        if hash in self._set:
            return False
        else:
            self._set.add(hash)
            return True

    def count(self):
        return len(self._set)
