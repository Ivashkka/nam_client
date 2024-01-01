import datastruct
import bcrypt
from getpass import getpass
from dataload import dload
from intapi import connect
from threading import Thread
from threading import Event
import signal

class _NAMclientcore(object):
    salt = b'$2b$12$ET4oX.YJCrU9OX92KWW2Ku'
    user = None
    settings = None
    responces_thread = None
    stop_event = Event()

    @staticmethod
    def start_core():
        signal.signal(signal.SIGTERM, _NAMclientcore.sigterm_handler)
        _NAMclientcore.init_connect()
        _NAMclientcore.user = _NAMclientcore.load_auth_data()
        _NAMclientcore.settings = _NAMclientcore.load_ai_settings()
        connect.connect_to_srv(auth_data=datastruct.to_dict(_NAMclientcore.user), settings=datastruct.to_dict(_NAMclientcore.settings))
        _NAMclientcore.responces_thread = Thread(target=_NAMclientcore.serve_responces, args=[])
        _NAMclientcore.responces_thread.start()
        _NAMclientcore.serve_client()

    @staticmethod
    def sigterm_handler(signal, frame):
        print('Received SIGTERM. Exiting gracefully...')
        _NAMclientcore.stop_event.set()

    @staticmethod
    def init_connect():
        connect_settings = dload.load_yaml("conf.yaml")["nam_client"]["connect"]
        connect.init_client(connect_settings)

    @staticmethod
    def serve_responces():
        while True:
            if _NAMclientcore.stop_event.is_set(): break
            response = datastruct.from_dict(connect.get_data(4096))
            if response == None: continue
            if response.type == datastruct.NAMDtype.AIresponse:
                print(response.message)

    @staticmethod
    def serve_client():
        while True:
            if _NAMclientcore.stop_event.is_set():
                _NAMclientcore.responces_thread.join()
                connect.close_conn()
                break
            command = input("nam> ")
            command_args = command.split(" ")
            match command_args[0]:
                case "-":
                    if len(command_args) < 2:
                        print("wrong command, try help")
                        continue
                    match command_args[1]:
                        case "change":
                            if len(command_args) < 3:
                                print("specify what to change, or try help")
                                continue
                            match command_args[2]:
                                case "model":
                                    _NAMclientcore.change_model()
                                case _:
                                    print(f"wrong argument {command_args[2]}, try help")
                        case "delete":
                            if len(command_args) < 3:
                                print("specify what to delete, or try help")
                                continue
                            if "con" in command_args[2]:
                                _NAMclientcore.delete_context()
                            else:
                                print(f"wrong argument {command_args[2]}, try help")
                        case "save":
                            _NAMclientcore.save_all_settings()
                        case "info":
                            _NAMclientcore.show_info()
                        case "stop":
                            print("nam client is stopping...")
                            _NAMclientcore.stop_event.set()
                        case "help":
                            print("change model - change model for ai\nsave - save all settings\ninfo - show all info\nhelp - show this info")
                        case _:
                            print(f"wrong argument {command_args[1]}, try help")
                case "":
                    pass
                case _:
                    connect.send_data(datastruct.to_dict(datastruct.AIrequest(command)))

    @staticmethod
    def encode_passwd(passwd):
        return bcrypt.hashpw(passwd, _NAMclientcore.salt).decode()

    @staticmethod
    def load_auth_data():
        auth = dload.load_json("auth.json")
        if auth != None:
            usr = datastruct.from_dict(auth)
            return usr
        else:
            print("enter auth data:")
            user_name = input("user_name: ")
            user_pass = getpass(f"password for user {user_name}: ").encode(encoding=connect.get_encoding())
            print("to save auth data, try '- save' or '- help' for more info")
            return datastruct.NAMuser(name=user_name, pass_hash=_NAMclientcore.encode_passwd(user_pass))

    @staticmethod
    def load_ai_settings():
        ai_settings = dload.load_yaml("conf.yaml")["ai_settings"]
        return datastruct.NAMSesSettings(model=datastruct.AImodels(ai_settings["model"]))
    
    @staticmethod
    def change_model():
        model = input("ai_model (gpt_35_turbo / gpt_35_long / gpt_4 / gpt_4_turbo): ")
        _NAMclientcore.settings.model = datastruct.AImodels(model)
        connect.send_data(datastruct.to_dict(_NAMclientcore.settings))

    @staticmethod
    def save_all_settings():
        dload.save_json("auth.json", datastruct.to_dict(_NAMclientcore.user))
        dload.yaml_change_single("conf.yaml", ["ai_settings","model"], _NAMclientcore.settings.model.value)

    @staticmethod
    def show_info():
        print(f"logged in as {_NAMclientcore.user.name}")
        print(f"current model: {_NAMclientcore.settings.model.value}")

    @staticmethod
    def delete_context():
        connect.send_data(datastruct.to_dict(datastruct.NAMcommand(datastruct.NAMCtype.ContextReset)))

def main():
    _NAMclientcore.start_core()

main()
