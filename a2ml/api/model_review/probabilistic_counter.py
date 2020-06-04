import math

from HLL import HyperLogLog

class ProbabilisticCounter(object):
    # error_rate: 1% = 0.01, 0.5% = 0.005 (min 0.005)
    def __init__(self, error_rate=0.005):
        self.error_rate = error_rate

        # error_rate = 1.04 / sqrt(m)
        # m = 2 ** p -> registers count
        # M(1)... M(m) = 0 -> registers

        p = int(math.ceil(math.log((1.04 / error_rate) ** 2, 2)))
        self.hll = HyperLogLog(p)

    # returns: True - value is new, False, value already included
    def add(self, value):
        return self.hll.add(value)

    def count(self):
        return math.floor(self.hll.cardinality())

def get_p(error_rate):
    return int(math.ceil(math.log((1.04 / error_rate) ** 2, 2)))
