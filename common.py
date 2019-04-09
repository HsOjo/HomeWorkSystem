import json
import os


def load_json(path, default=None):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf8') as io:
            data = json.load(io)
    else:
        data = default

    return data


def save_json(path, data):
    with open(path, 'w', encoding='utf8') as io:
        json.dump(data, io, ensure_ascii=False, indent=4)
