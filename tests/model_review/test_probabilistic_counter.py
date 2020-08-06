from a2ml.api.model_review.probabilistic_counter import ProbabilisticCounter

class TestProbabilisticCounter(object):
    def test_error_rate(self):
        counter = ProbabilisticCounter()
        offset = 123456789

        for i in range(0, 100):
            counter.add(str(offset + i))
        assert counter.count() == 100

        false_negatives = 0
        for i in range(0, 100):
            if counter.add(str(offset + i)):
                false_negatives += 1
        assert false_negatives == 0
        assert counter.count() == 100

        false_positives = 0
        total = 0
        for i in range(200, 300):
            total += 1
            if not counter.add(str(offset + i)):
                false_positives += 1
        assert false_positives / total == 0
        assert counter.count() == 200
