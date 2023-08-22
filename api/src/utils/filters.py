from collections.abc import Sequence


def filter_keys(obj: dict, fields: Sequence[str] | None, parent: dict | None = None):
    if isinstance(obj, dict) and fields:
        for k, v in obj.copy().items():
            if k not in fields and not isinstance(v, dict):
                del obj[k]
            else:
                filter_keys(v, fields, obj)
        if obj == {} and parent is not None:
            for pk, pv in parent.copy().items():
                if pv == {}:
                    del parent[pk]
    return obj


def filter_langs(comic: dict, languages: Sequence[str]):
    translations: dict = comic['translations']
    for lang_code, _content in translations.copy().items():
        if lang_code not in languages:
            del comic['translations'][lang_code]
    return comic
