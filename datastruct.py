########################## datastruct.py ##########################

import enum

class NAMDtype(enum.Enum): # primary key to transfer data between server and client
    AIrequest       =   "AIrequest"
    AIresponse      =   "AIresponse"
    NAMuser         =   "NAMuser"
    NAMSesSettings  =   "NAMSesSettings"
    NAMcommand      =   "NAMcommand"
    NAMexcode       =   "NAMexcode"

class NAMCtype(enum.Enum): # Types of commands between nam srv and nam client
    ContextReset    =   "ContextReset"
    TestConn        =   "TestConn"

class AImodels(enum.Enum): # supported ai models
    GPT35turbo  =   "gpt_35_turbo"
    GPT35long   =   "gpt_35_long"
    GPT4        =   "gpt_4"
    GPT4turbo   =   "gpt_4_turbo"

class NAMEtype(enum.Enum): # main exit codes
    Success     =   0
    IntFail     =   1 # Internal Fail
    ConTimeOut  =   2
    SrvConFail  =   3 # Failed to comunicate with server
    IntConFail  =   4 # Failed to comunicate via unix named socket
    ClientFail  =   5 # Server's reply about wrong data from client
    SrvFail     =   6 # wrong data from server or IntFail on server
    Deny        =   7
    InitConnFail=   8 # Fail in connect.py init_socket

class NAMuser: # auth data
    __slots__ = ['type', 'name', 'pass_hash']
    def __init__(self, name=None, pass_hash=None):
        self.type = NAMDtype.NAMuser
        self.name = name
        self.pass_hash = pass_hash

class AIrequest:
    __slots__ = ['message', 'type']
    def __init__(self, message=None):
        self.message = message
        self.type = NAMDtype.AIrequest

class AIresponse:
    __slots__ = ['message', 'type']
    def __init__(self, message=None):
        self.message = message
        self.type = NAMDtype.AIresponse

class NAMSesSettings:
    __slots__ = ['model', 'type']
    def __init__(self, model=None):
        self.model = model
        self.type = NAMDtype.NAMSesSettings

class NAMcommand:
    __slots__ = ['command', 'type']
    def __init__(self, command=None):
        self.command = command
        self.type = NAMDtype.NAMcommand

class NAMexcode:
    __slots__ = ['code', 'type']
    def __init__(self, code=None):
        self.code = code
        self.type = NAMDtype.NAMexcode

def to_dict(obj): #convert any class object to dictionary
    if not hasattr(obj, 'type'): return None
    obj_dict = {}
    for field in obj.__slots__:
        if field == 'type' or field == 'model' or field == 'command' or field == 'code':
            obj_dict[field] = getattr(obj, field).value
            continue
        obj_dict[field] = getattr(obj, field)
    return obj_dict

def from_dict(obj_dict): #create class object from given dictionary
    if type(obj_dict) is not dict or not 'type' in obj_dict: return None
    obj = globals()[obj_dict['type']]()
    for field in obj_dict:
        if field == 'type':
            setattr(obj, field, NAMDtype(obj_dict[field]))
            continue
        if field == 'model':
            setattr(obj, field, AImodels(obj_dict[field]))
            continue
        if field == 'command':
            setattr(obj, field, NAMCtype(obj_dict[field]))
            continue
        if field == 'code':
            setattr(obj, field, NAMEtype(obj_dict[field]))
            continue
        setattr(obj, field, obj_dict[field])
    return obj
