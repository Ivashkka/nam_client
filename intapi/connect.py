import socket
import json

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
        if not _NAMclient.init: return
        _NAMclient.client_sock.connect((_NAMclient.server_ip, _NAMclient.server_port))
        _NAMclient.send_data({"auth_data": auth_data, "settings": settings})

    @staticmethod
    def get_data(bytes):
        if not _NAMclient.init: return {"corrupted": "client was not inited"}
        try:
            return json.loads(_NAMclient.client_sock.recv(bytes).decode())
        except Exception as e:
            return None
    
    @staticmethod
    def send_data(data):
        if not _NAMclient.init: return
        _NAMclient.client_sock.send(json.dumps(data).encode(encoding=_NAMclient.encoding))
    
    @staticmethod
    def close_conn():
        if not _NAMclient.init: return
        _NAMclient.client_sock.close()

def init_client(client_settings):
    _NAMclient.init_socket(client_settings["server_ip"], client_settings["server_port"], client_settings["encoding"])

def connect_to_srv(auth_data, settings):
    _NAMclient.connect_to_srv(auth_data, settings)

def close_conn():
    _NAMclient.close_conn()

def send_data(data):
    return _NAMclient.send_data(data)

def get_data(bytes):
    return _NAMclient.get_data(bytes)

def get_encoding():
    return _NAMclient.encoding
