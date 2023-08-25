from collections.abc import Sequence


def filter_keys(obj: dict, keys: Sequence[str], parent: dict | None = None):
    """
    Recursively delete keys from dict that are not passed in 'keys' parameter
    and after delete empty dicts.
    """
    if isinstance(obj, dict) and keys:
        for k, v in obj.copy().items():
            if k not in keys and not isinstance(v, dict):
                del obj[k]
            else:
                filter_keys(v, keys, obj)
        if obj == {} and parent is not None:
            for pk, pv in parent.copy().items():
                if pv == {}:
                    del parent[pk]
    return obj
