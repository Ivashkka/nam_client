import enum

class NAMDtype(enum.Enum): # primary key to transfer data between server and client
    AIrequest       =   "AIrequest"
    AIresponse      =   "AIresponse"
    NAMuser         =   "NAMuser"
    NAMSesSettings  =   "NAMSesSettings"

class AImodels(enum.Enum):
    GPT35turbo  =   "gpt_35_turbo"
    GPT35long   =   "gpt_35_long"
    GPT4        =   "gpt_4"
    GPT4turbo   =   "gpt_4_turbo"

#basic classes for user, response, request and session:

class NAMuser:
    __slots__ = ['type', 'name', 'pass_hash', 'uuid']
    def __init__(self, name=None, pass_hash=None, uuid=None):
        self.type = NAMDtype.NAMuser
        self.name = name
        self.pass_hash = pass_hash
        self.uuid = uuid

class AIrequest:
    __slots__ = ['message', 'uuid', 'type']
    def __init__(self, message=None, uuid=None):
        self.message = message
        self.uuid = uuid
        self.type = NAMDtype.AIrequest

class AIresponse:
    __slots__ = ['message', 'uuid', 'type']
    def __init__(self, message=None, uuid=None):
        self.message = message
        self.uuid = uuid
        self.type = NAMDtype.AIresponse

class NAMSesSettings:
    __slots__ = ['model', 'type']
    def __init__(self, model=None):
        self.model = model
        self.type = NAMDtype.NAMSesSettings

def to_dict(obj): #convert any class object to dictionary
    if not hasattr(obj, 'type'): return
    dict = {}
    for field in obj.__slots__:
        dict[field] = getattr(obj, field)
        if field == 'type' or field == 'model':
            dict[field] = getattr(obj, field).value
    return dict

def from_dict(dict): #create class object from given dictionary
    if not 'type' in dict: return
    obj = globals()[dict['type']]()
    for field in dict:
        setattr(obj, field, dict[field])
        if field == 'type':
            setattr(obj, field, NAMDtype(dict[field]))
        if field == 'model':
            setattr(obj, field, AImodels(dict[field]))
    return obj
