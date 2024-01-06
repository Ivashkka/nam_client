import socket
import json
import enum
import os

class NAMconcode(enum.Enum):
    Success     =   0
    Timeout     =   1
    Fail        =   2

class _NAMclient(object): #basic clientside networking structure
    init = False
    client_sock = None
    local_sock = None
    uspath = None
    encoding = None
    server_ip = None
    server_port = None

    INTERACT = False #will change in future

    @staticmethod
    def init_socket(server_ip, server_port, encoding, unix_socket_path, interact): #create socket
        _NAMclient.INTERACT = interact
        _NAMclient.client_sock = socket.socket()
        _NAMclient.client_sock.settimeout(3)
        if not _NAMclient.INTERACT:
            _NAMclient.uspath = unix_socket_path
            _NAMclient.close_local_sock()
            _NAMclient.local_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            _NAMclient.local_sock.bind(unix_socket_path)
            _NAMclient.local_sock.listen(1)
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

    @staticmethod
    def get_ctl_connect():
        if not _NAMclient.init: return None
        ctl_conn, ctl_address = _NAMclient.local_sock.accept()
        return ctl_conn

    @staticmethod
    def get_ctl_command(ctl_conn, bytes):
        if not _NAMclient.init: return None
        try:
            return ctl_conn.recv(bytes).decode()
        except Exception as e:
            return NAMconcode.Fail
    
    @staticmethod
    def send_ctl_answer(ctl_conn, data):
        if not _NAMclient.init: return None
        try:
            ctl_conn.send(data.encode(encoding=_NAMclient.encoding))
        except Exception as e:
            return NAMconcode.Fail
        
    def close_ctl_conn(ctl_conn):
        if not _NAMclient.init: return None
        ctl_conn.close()

    @staticmethod
    def close_local_sock():
        if not _NAMclient.init: return None
        try:
            os.unlink(_NAMclient.uspath)
        except Exception as e:
            if os.path.exists(_NAMclient.uspath):
                raise Exception(f"can't remove old {_NAMclient.uspath} socket!")

def init_client(client_settings, interact):
    _NAMclient.init_socket(client_settings["server_ip"], client_settings["server_port"], client_settings["encoding"], client_settings["unix_socket_path"], interact)

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

def close_local_sock():
    _NAMclient.close_local_sock()

def get_ctl_connect():
    return _NAMclient.get_ctl_connect()

def send_ctl_answer(ctl_conn, data):
    _NAMclient.send_ctl_answer(ctl_conn, data)

def get_ctl_command(ctl_conn, bytes):
    return _NAMclient.get_ctl_command(ctl_conn, bytes)

def close_ctl_conn():
    return _NAMclient.close_ctl_conn()

def get_encoding():
    return _NAMclient.encoding
