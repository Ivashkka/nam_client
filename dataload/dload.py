import yaml
import json

class _YAMLload(object):
    @staticmethod
    def load(path):
        with open(path) as f:
            data = yaml.safe_load(f)
        return data
    def save(path, data):
        with open(path, 'w') as f:
            yaml.safe_dump(data, f)
    def change_single(path, key_tree, value):
        data = _YAMLload.load(path)
        data[key_tree[-2]][key_tree[-1]] = value
        _YAMLload.save(path, data)

class _JSONload(object):
    @staticmethod
    def load(path):
        try:
            with open(path) as f:
                data = json.load(f)
            return data
        except Exception as e:
            return None
    def save(path, data):
        with open(path, 'w') as f:
            json.dump(data, f)

class _TXTload(object):
    @staticmethod
    def load(path):
        try:
            with open(path) as f:
                data = f.read()
            return data
        except Exception as e:
            return None

def load_yaml(path):
    return _YAMLload.load(path)

def save_yaml(path, data):
    _YAMLload.save(path, data)

def yaml_change_single(path, key, value):
    _YAMLload.change_single(path, key, value)

def load_json(path):
    return _JSONload.load(path)

def save_json(path, data):
    _JSONload.save(path=path, data=data)

def load_txt(path):
    return _TXTload.load(path)
