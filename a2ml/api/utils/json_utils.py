import json
import numpy as np
import math
import numbers


def is_nan(x):
    return (x is np.nan or x != x)

def convert_simple_numpy_type(obj):
    if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
        np.int16, np.int32, np.int64, np.uint8,
        np.uint16, np.uint32, np.uint64)):
        return int(obj)
    elif isinstance(obj, (np.float_, np.float16, np.float32,
        np.float64)):
        return float(obj)
    elif isinstance(obj, (np.bool_)):
        return bool(obj)

    # elif isinstance(obj,(np.ndarray,)): #### This is the fix
    #     return obj.tolist()

    return None

class NumpyJSONEncoder(json.JSONEncoder):
    """ Special json encoder for numpy types """
    def default(self, obj):
        res = convert_simple_numpy_type(obj)
        if res is not None:
            return res

        return json.JSONEncoder.default(self, obj)

def convert_nan_inf(params):
    if type(params) is dict:
        for key, value in params.items():
            params[key] = convert_nan_inf(value)
    elif type(params) is list:
        for idx, value in enumerate(params):
            params[idx] = convert_nan_inf(value)
    else:
        if isinstance(params, numbers.Number) and math.isinf(params):
            params = None
        if is_nan(params):
            params = None

    return params

def convert_numpy_types(params):
    if params is None:
        return params

    if type(params) is dict:
        for key, value in list(params.items()):
            res = convert_simple_numpy_type(key)
            if res is not None:
                del params[key]
                key = res
                
            params[key] = convert_numpy_types(value)
    elif type(params) is list:
        for idx, value in enumerate(params):
            params[idx] = convert_numpy_types(value)
    else:
        if isinstance(params, numbers.Number) and math.isinf(params):
            params = None
        elif is_nan(params):
            params = None
        else:
            res = convert_simple_numpy_type(params)
            if res is not None:
                params = res

    return params

def json_dumps_np(data, allow_nan=False):
    if not allow_nan:
        data = convert_nan_inf(data)

    data = convert_numpy_types(data)

    return json.dumps(data, cls=NumpyJSONEncoder, allow_nan=allow_nan)
