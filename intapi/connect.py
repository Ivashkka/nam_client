import socket
import json
import enum

class NAMconcode(enum.Enum):
    Success     =   0
    Timeout     =   1
    Fail        =   2

class _NAMclient(object): #basic clientside networking structure

    init = False
    client_sock = None
    encoding = None
    server_ip = None
    server_port = None

    @staticmethod
    def init_socket(server_ip, server_port, encoding): #create socket
        _NAMclient.client_sock = socket.socket()
        _NAMclient.client_sock.settimeout(3)
        _NAMclient.server_ip = server_ip
        _NAMclient.server_port = server_port
        _NAMclient.encoding = encoding
        _NAMclient.init = True

    @staticmethod
    def connect_to_srv(auth_data, settings): #connect to srv and send auth data
        if not _NAMclient.init: return None
        try:
            _NAMclient.client_sock.connect((_NAMclient.server_ip, _NAMclient.server_port))
            return _NAMclient.send_data({"auth_data": auth_data, "settings": settings})
        except socket.timeout:
            return NAMconcode.Fail
        except Exception as e:
            return NAMconcode.Fail

    @staticmethod
    def get_data(bytes):
        if not _NAMclient.init: return None
        try:
            return json.loads(_NAMclient.client_sock.recv(bytes).decode())
        except socket.timeout:
            return NAMconcode.Timeout
        except Exception as e:
            return NAMconcode.Fail

    @staticmethod
    def send_data(data):
        if not _NAMclient.init: return None
        try:
            _NAMclient.client_sock.send(json.dumps(data).encode(encoding=_NAMclient.encoding))
            return NAMconcode.Success
        except Exception as e:
            return NAMconcode.Fail
    
    @staticmethod
    def close_conn():
        if not _NAMclient.init: return None
        _NAMclient.client_sock.close()

    @staticmethod
    def open_new_sock():
        if not _NAMclient.init: return None
        _NAMclient.client_sock = socket.socket()
        _NAMclient.client_sock.settimeout(3)


def init_client(client_settings):
    _NAMclient.init_socket(client_settings["server_ip"], client_settings["server_port"], client_settings["encoding"])

def connect_to_srv(auth_data, settings):
    return _NAMclient.connect_to_srv(auth_data, settings)

def open_new_sock():
    _NAMclient.open_new_sock()

def close_conn():
    _NAMclient.close_conn()

def send_data(data):
    return _NAMclient.send_data(data)

def get_data(bytes):
    return _NAMclient.get_data(bytes)

def get_encoding():
    return _NAMclient.encoding
