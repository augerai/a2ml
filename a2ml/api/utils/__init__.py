from collections.abc import Iterable

def to_list(obj):
    if obj:
        if isinstance(obj, Iterable) and not isinstance(obj, str):
            return list(obj)
        else:
            return [obj]
    else:
        return []

def dict_dig(obj, *path):
    curr = obj
    i = 0

    while curr and i < len(path) and isinstance(curr, dict):
        curr = curr.get(path[i], None)
        i += 1

    return curr
