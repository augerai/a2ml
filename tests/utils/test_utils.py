from a2ml.api.utils import dict_dig


class TestUtils(object):
    def test_dict_dig(self):
      d = { 'a': {'b': { 'c': 123 }}}

      assert dict_dig(d, 'a', 'b', 'c') == 123
      assert dict_dig(d, 'a', 'b', 'd') == None
      assert dict_dig(d, 'aa', 'bb') == None
