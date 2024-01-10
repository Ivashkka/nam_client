########################## dload.py ##########################

import yaml
import json

class _YAMLload(object): # class for working with yaml files
    @staticmethod
    def load(path):
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
            return data
        except Exception as e:
            return None
    def save(path, data):
        try:
            with open(path, 'w') as f:
                yaml.safe_dump(data, f)
            return True
        except Exception as e:
            return False
    def change_single(path, key_tree, value): # bad implementation, will change in future
        data = _YAMLload.load(path)
        if data == None: return False
        data[key_tree[-2]][key_tree[-1]] = value
        return _YAMLload.save(path, data)

class _JSONload(object): # class for working with json files
    @staticmethod
    def load(path):
        try:
            with open(path) as f:
                data = json.load(f)
            return data
        except Exception as e:
            return None
    def save(path, data):
        try:
            with open(path, 'w') as f:
                json.dump(data, f)
            return True
        except Exception as e:
            return False

class _TXTload(object): # class for working with all txt files
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
    return _YAMLload.save(path, data)

def yaml_change_single(path, key, value): # change single key in yaml
    return _YAMLload.change_single(path, key, value)

def load_json(path):
    return _JSONload.load(path)

def save_json(path, data):
    return _JSONload.save(path=path, data=data)

def load_txt(path):
    return _TXTload.load(path)

def test_file(path): # check if file exists and readable
    if _TXTload.load(path) == None: return False
    else: return True
