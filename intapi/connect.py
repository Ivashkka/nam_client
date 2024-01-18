########################## connect.py ##########################

import socket
import json
import enum
import os

class NAMconcode(enum.Enum): # execution codes
    Success     =   0
    Timeout     =   1
    Fail        =   2
    JsonFail    =   3
    OldSock     =   4

class _NAMclient(object): #basic clientside networking structure
    init = False
    client_sock = None
    local_sock = None
    uspath = None
    encoding = None
    server_ip = None
    server_port = None

    INTERACT = True

    @staticmethod
    def init_socket(server_ip, server_port, encoding, unix_socket_path, interact): #create socket
        init_stages_codes = []
        _NAMclient.INTERACT = interact
        try:
            _NAMclient.client_sock = socket.socket()
            _NAMclient.client_sock.settimeout(3)
            init_stages_codes.append(NAMconcode.Success)
        except:
            print("failed to create network socket")
            init_stages_codes.append(NAMconcode.Fail)
        if not _NAMclient.INTERACT:
            _NAMclient.uspath = unix_socket_path
            init_stages_codes.append(_NAMclient.close_local_sock())
            try:
                _NAMclient.local_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                _NAMclient.local_sock.bind(unix_socket_path)
                _NAMclient.local_sock.listen(1)
                _NAMclient.local_sock.settimeout(3)
                init_stages_codes.append(NAMconcode.Success)
            except:
                print("failed to bind unix named socket")
                init_stages_codes.append(NAMconcode.Fail)
        _NAMclient.server_ip = server_ip
        _NAMclient.server_port = server_port
        _NAMclient.encoding = encoding
        if NAMconcode.Fail not in init_stages_codes:
            _NAMclient.init = True
            return NAMconcode.Success
        else: return NAMconcode.Fail

    @staticmethod
    def connect_to_srv(auth_data, settings): #connect to srv and send auth data
        if not _NAMclient.init: return NAMconcode.Fail
        try:
            _NAMclient.client_sock.connect((_NAMclient.server_ip, _NAMclient.server_port))
            return _NAMclient.send_data({"auth_data": auth_data, "settings": settings})
        except socket.error as e:
            if e.errno == 10056:
                print(NAMconcode.OldSock)
                return NAMconcode.OldSock
            return NAMconcode.Fail

    @staticmethod
    def get_data(bytes):
        if not _NAMclient.init: return NAMconcode.Fail
        try:
            data = _NAMclient.client_sock.recv(bytes)
            if not data: return NAMconcode.Fail
            return json.loads(data.decode())
        except socket.timeout:
            return NAMconcode.Timeout
        except json.JSONDecodeError as e:
            return NAMconcode.JsonFail
        except Exception as e:
            return NAMconcode.Fail

    @staticmethod
    def send_data(data):
        if not _NAMclient.init: return NAMconcode.Fail
        try:
            _NAMclient.client_sock.send(json.dumps(data).encode(encoding=_NAMclient.encoding))
            return NAMconcode.Success
        except socket.timeout:
            return NAMconcode.Timeout
        except:
            return NAMconcode.Fail
    
    @staticmethod
    def close_conn(): # close existing srv connection
        if not _NAMclient.init: return NAMconcode.Fail
        _NAMclient.client_sock.close()
        _NAMclient.client_sock = None
        return NAMconcode.Success

    @staticmethod
    def open_new_sock(): # open new network socket
        if not _NAMclient.init: return NAMconcode.Fail
        _NAMclient.client_sock = socket.socket()
        _NAMclient.client_sock.settimeout(3)
        return NAMconcode.Success

    @staticmethod
    def get_ctl_connect(): # get unix named socket connection
        if not _NAMclient.init: return NAMconcode.Fail
        try:
            ctl_conn, ctl_address = _NAMclient.local_sock.accept()
            return ctl_conn
        except socket.timeout:
            return NAMconcode.Timeout
        except Exception as e:
            return NAMconcode.Fail

    @staticmethod
    def get_ctl_command(ctl_conn, bytes): # get unix named socket data
        if not _NAMclient.init: return NAMconcode.Fail
        try:
            return ctl_conn.recv(bytes).decode()
        except socket.timeout:
            return NAMconcode.Timeout
        except:
            return NAMconcode.Fail
    
    @staticmethod
    def send_ctl_answer(ctl_conn, data): # send data to unix named socket
        if not _NAMclient.init: return NAMconcode.Fail
        try:
            ctl_conn.send(data.encode(encoding=_NAMclient.encoding))
            return NAMconcode.Success
        except socket.timeout:
            return NAMconcode.Timeout
        except:
            return NAMconcode.Fail
        
    def close_ctl_conn(ctl_conn): # close connection over unix named socket
        if not _NAMclient.init: return NAMconcode.Fail
        ctl_conn.close()
        ctl_conn = None
        return NAMconcode.Success

    @staticmethod
    def close_local_sock(): # close unix named socket
        try:
            os.unlink(_NAMclient.uspath)
            return NAMconcode.Success
        except Exception as e:
            if os.path.exists(_NAMclient.uspath):
                print(f"can't remove old {_NAMclient.uspath} socket!")
                return NAMconcode.Fail
            return NAMconcode.Success

def init_client(client_settings, interact):
    return _NAMclient.init_socket(client_settings["server_ip"], client_settings["server_port"], client_settings["encoding"], client_settings["unix_socket_path"], interact)

def connect_to_srv(auth_data, settings):
    return _NAMclient.connect_to_srv(auth_data, settings)

def open_new_sock():
    return _NAMclient.open_new_sock()

def close_conn():
    return _NAMclient.close_conn()

def send_data(data):
    return _NAMclient.send_data(data)

def get_data(bytes):
    return _NAMclient.get_data(bytes)

def close_local_sock():
    return _NAMclient.close_local_sock()

def get_ctl_connect():
    return _NAMclient.get_ctl_connect()

def send_ctl_answer(ctl_conn, data):
    return _NAMclient.send_ctl_answer(ctl_conn, data)

def get_ctl_command(ctl_conn, bytes):
    return _NAMclient.get_ctl_command(ctl_conn, bytes)

def close_ctl_conn(ctl_conn):
    return _NAMclient.close_ctl_conn(ctl_conn)

def get_encoding():
    return _NAMclient.encoding
