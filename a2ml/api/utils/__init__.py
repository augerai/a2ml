from collections.abc import Iterable

def to_list(obj):
    if obj:
        if isinstance(obj, Iterable) and not isinstance(obj, str):
            return list(obj)
        else:
            return [obj]
    else:
        return []
