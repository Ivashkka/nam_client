import enum

class NAMDtype(enum.Enum): # primary key to transfer data between server and client
    AIrequest       =   "AIrequest"
    AIresponse      =   "AIresponse"
    NAMuser         =   "NAMuser"
    NAMSesSettings  =   "NAMSesSettings"
    NAMcommand      =   "NAMcommand"

class NAMCtype(enum.Enum):
    ContextReset    =   "ContextReset"
    TestConn        =   "TestConn"

class AImodels(enum.Enum):
    GPT35turbo  =   "gpt_35_turbo"
    GPT35long   =   "gpt_35_long"
    GPT4        =   "gpt_4"
    GPT4turbo   =   "gpt_4_turbo"

#basic classes for user, response, request and session:

class NAMuser:
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

def to_dict(obj): #convert any class object to dictionary
    if not hasattr(obj, 'type'): return None
    obj_dict = {}
    for field in obj.__slots__:
        if field == 'type' or field == 'model' or field == 'command':
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
        setattr(obj, field, obj_dict[field])
    return obj
