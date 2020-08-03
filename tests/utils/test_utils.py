from a2ml.api.utils import dict_dig
from a2ml.api.utils.json_utils import json_dumps_np
import numpy as np


class TestUtils(object):
    def test_dict_dig(self):
      d = { 'a': {'b': { 'c': 123 }}}

      assert dict_dig(d, 'a', 'b', 'c') == 123
      assert dict_dig(d, 'a', 'b', 'd') == None
      assert dict_dig(d, 'aa', 'bb') == None

    def test_json_dumps_np(self):
        data = {
            'data1': 123,
            'data2': '456',
            'data3': float('NaN'),
            'data31': float('INF'),
            'data31': float('-INF'),
            'data4': np.nan,
            'data5': np.NaN,
            'data6': np.inf
        }
        res = json_dumps_np(data, allow_nan=False)
        assert res == '{"data1": 123, "data2": "456", "data3": null, "data31": null, "data4": null, "data5": null, "data6": null}'
