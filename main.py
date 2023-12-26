import uuid
import datastruct
import bcrypt
from getpass import getpass
from dataload import dload
from intapi import connect

class _NAMclientcore(object):
    salt = b'$2b$12$ET4oX.YJCrU9OX92KWW2Ku'
    user = None
    settings = None

    @staticmethod
    def start_core():
        client_settings = dload.load_yaml("conf.yaml")["nam_client"]
        connect.init_client(client_settings)
        _NAMclientcore.user = _NAMclientcore.get_auth_data()
        _NAMclientcore.settings = _NAMclientcore.get_ai_settings()
        connect.connect_to_srv(auth_data=datastruct.to_dict(_NAMclientcore.user), settings=datastruct.to_dict(_NAMclientcore.settings))
        _NAMclientcore.serve_client()

    @staticmethod
    def serve_client():
        while True:
            message = _NAMclientcore.get_message()
            connect.send_data(datastruct.to_dict(message))
            response = datastruct.from_dict(connect.get_data(1024))
            print(response.message)

    @staticmethod
    def encode_passwd(passwd):
        return bcrypt.hashpw(passwd, _NAMclientcore.salt).decode()

    @staticmethod
    def get_auth_data():
        user_name = input("user_name: ")
        user_pass = getpass("user_pass: ").encode(encoding=connect.get_encoding())
        return datastruct.NAMuser(name=user_name, pass_hash=_NAMclientcore.encode_passwd(user_pass), uuid=None)

    @staticmethod
    def get_ai_settings():
        model = input("ai_model (gpt_35_turbo / gpt_35_long / gpt_4 / gpt_4_turbo): ")
        return datastruct.NAMSesSettings(model=datastruct.AImodels(model))

    @staticmethod
    def get_message():
       return datastruct.AIrequest(input("request: "), uuid.uuid4().hex)

def main():
    _NAMclientcore.start_core()

main()
