import json

def convert_simple_numpy_type(obj):
    import numpy as np

    if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
        np.int16, np.int32, np.int64, np.uint8,
        np.uint16, np.uint32, np.uint64)):
        return int(obj)
    elif isinstance(obj, (np.float_, np.float16, np.float32,
        np.float64)):
        return float(obj)

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

def json_dumps_np(data, allow_nan=True):
    return json.dumps(data, cls=NumpyJSONEncoder, allow_nan=allow_nan)
