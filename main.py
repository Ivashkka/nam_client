import datastruct
import bcrypt
import time
from getpass import getpass
from dataload import dload
from intapi import connect
from threading import Thread
from threading import Event
import signal
import setproctitle
import sys

class _NAMclientcore(object):
    salt = b'$2b$12$ET4oX.YJCrU9OX92KWW2Ku'
    conf_yaml = "conf.yaml"
    auth_json = "auth.json"
    user = None
    settings = None
    responces_thread = None
    reconnect_thread = None
    stop_event = Event()
    reconnect_event = Event()

    commads_dict = {"change model": "change_model", "delete con":"delete_context", "info":"show_info",
                    "save":"save_all_settings", "stop":"stop_all", "recon":"reconnect_to_srv", "help":"show_help"}
    
    INTERACT = False #will change in future

    @staticmethod
    def start_core():
        signal.signal(signal.SIGTERM, _NAMclientcore.sigterm_handler)
        setproctitle.setproctitle('nam_client_python')
        _NAMclientcore.solve_cli_args()
        _NAMclientcore.init_connect()
        _NAMclientcore.user = _NAMclientcore.load_auth_data()
        _NAMclientcore.settings = _NAMclientcore.load_ai_settings()
        excode = connect.connect_to_srv(auth_data=datastruct.to_dict(_NAMclientcore.user), settings=datastruct.to_dict(_NAMclientcore.settings))
        if excode == connect.NAMconcode.Fail:
            _NAMclientcore.reconnect_event.set()
        _NAMclientcore.responces_thread = Thread(target=_NAMclientcore.serve_responces, args=[])
        _NAMclientcore.responces_thread.start()
        _NAMclientcore.serve_client()

    @staticmethod
    def solve_cli_args():
        if "interact" in sys.argv:
            _NAMclientcore.INTERACT = True
        if len(sys.argv) > 1:
            if dload.load_txt(str(sys.argv[1])+"/conf.yaml") != None:
                _NAMclientcore.conf_yaml = str(sys.argv[1])+"/conf.yaml"
                _NAMclientcore.auth_json = str(sys.argv[1])+"/auth.json"
            else:
                if str(sys.argv[1]) != "interact": raise Exception(f"can't find conf.yaml in {sys.argv[1]} dir!")

    @staticmethod
    def send_output(data, ctl_conn = None):
        if ctl_conn == None:
            print(data)
        else:
            connect.send_ctl_answer(ctl_conn, data)

    @staticmethod
    def get_input(prompt = "nam> ", ctl_conn = None):
        if ctl_conn == None:
            print(prompt, end="")
            return input()
        elif ctl_conn != None:
            _NAMclientcore.send_output(f"IEN {prompt}", ctl_conn)
            return connect.get_ctl_command(ctl_conn, 4096)

    @staticmethod
    def sigterm_handler(signal, frame):
        print('Received SIGTERM. Exiting gracefully...')
        _NAMclientcore.stop_event.set()

    @staticmethod
    def init_connect():
        connect_settings = dload.load_yaml(_NAMclientcore.conf_yaml)["nam_client"]["connect"]
        connect.init_client(connect_settings, _NAMclientcore.INTERACT)

    @staticmethod
    def encode_passwd(passwd):
        return bcrypt.hashpw(passwd, _NAMclientcore.salt).decode()

    @staticmethod
    def load_auth_data():
        auth = dload.load_json(_NAMclientcore.auth_json)
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
        ai_settings = dload.load_yaml(_NAMclientcore.conf_yaml)["ai_settings"]
        return datastruct.NAMSesSettings(model=datastruct.AImodels(ai_settings["model"]))




    @staticmethod
    def serve_responces():
        while True:
            if _NAMclientcore.stop_event.is_set(): break
            if _NAMclientcore.reconnect_event.is_set(): continue
            raw_resp = connect.get_data(4096)
            if raw_resp == connect.NAMconcode.Fail:
                _NAMclientcore.reconnect_event.set()
                continue
            response = datastruct.from_dict(raw_resp)
            if response == None: continue
            if response.type == datastruct.NAMDtype.AIresponse:
                print(response.message)

    @staticmethod
    def recon_async():
        while True:
            if _NAMclientcore.stop_event.is_set():
                break
            excode = connect.connect_to_srv(auth_data=datastruct.to_dict(_NAMclientcore.user), settings=datastruct.to_dict(_NAMclientcore.settings))
            if excode == connect.NAMconcode.Success:
                _NAMclientcore.reconnect_event.clear()
                print("reconnected")
                break
            time.sleep(2)




    @staticmethod
    def serve_client():
        while True:
            if _NAMclientcore.stop_event.is_set():
                _NAMclientcore.responces_thread.join()
                if _NAMclientcore.reconnect_thread != None: _NAMclientcore.reconnect_thread.join()
                connect.close_conn()
                if not _NAMclientcore.INTERACT: connect.close_local_sock()
                print("done")
                break
            if _NAMclientcore.reconnect_event.is_set():
                if _NAMclientcore.reconnect_thread == None or not _NAMclientcore.reconnect_thread.is_alive():
                    connect.close_conn()
                    connect.open_new_sock()
                    _NAMclientcore.reconnect_thread = Thread(target=_NAMclientcore.recon_async, args=[])
                    _NAMclientcore.reconnect_thread.start()

            if _NAMclientcore.INTERACT: excode = _NAMclientcore.direct_interaction()
            else:
                ctl_conn = connect.get_ctl_connect()
                excode = _NAMclientcore.ctl_interaction(ctl_conn)
                _NAMclientcore.send_output("END", ctl_conn)
                connect.close_ctl_conn(ctl_conn)

            if excode == connect.NAMconcode.Fail:
                _NAMclientcore.reconnect_to_srv()


            # if not _NAMclientcore.INTERACT:
            #     ctl_conn = connect.get_ctl_connect()
            #     command = connect.get_ctl_command(ctl_conn)
            # else:
            #     print("nam> ", end="")
            #     command = input()
            # command_args = command.split(" ")
            # excode = None
            # answer = ""
            # match command_args[0]:
            #     case "-":
            #         if len(command_args) < 2:
            #             answer = "wrong command, try help"
            #             continue
            #         match command_args[1]:
            #             case "change":
            #                 if len(command_args) < 3:
            #                     answer = "specify what to change, or try help"
            #                     continue
            #                 match command_args[2]:
            #                     case "model":
            #                         excode = _NAMclientcore.change_model()
            #                     case _:
            #                         answer = f"wrong argument {command_args[2]}, try help"
            #             case "delete":
            #                 if len(command_args) < 3:
            #                     answer = "specify what to delete, or try help"
            #                     continue
            #                 if "con" in command_args[2]:
            #                     excode = _NAMclientcore.delete_context()
            #                 else:
            #                     answer = f"wrong argument {command_args[2]}, try help"
            #             case "save":
            #                 _NAMclientcore.save_all_settings()
            #             case "info":
            #                 _NAMclientcore.show_info()
            #             case "stop":
            #                 print("nam client is stopping...")
            #                 _NAMclientcore.stop_event.set()
            #             case "recon":
            #                 answer = "reconnecting to the server..."
            #                 _NAMclientcore.reconnect_event.set()
            #             case "file":
            #                 reqlist = []
            #                 req = ""
            #                 for i in range(2, len(command_args)):
            #                     fdata = dload.load_txt(command_args[i])
            #                     if fdata != None:
            #                         req += f"{command_args[i]} content:\n{fdata}\n\n"
            #                     else:
            #                         reqlist = command_args[i:]
            #                         break
            #                 if req == "":
            #                     answer = "you need to specify at least one file"
            #                 else:
            #                     req += f"\nAnswer my question taking into account the contents of the files. My request: {" ".join(reqlist)}"
            #                     excode = connect.send_data(datastruct.to_dict(datastruct.AIrequest(req)))
            #             case "help":
            #                 answer = ""
            #             case _:
            #                 answer = f"wrong argument {command_args[1]}, try help"
            #     case "":
            #         pass
            #     case _:
            #         excode = connect.send_data(datastruct.to_dict(datastruct.AIrequest(command)))
            # if excode == connect.NAMconcode.Fail:
            #     _NAMclientcore.reconnect_event.set()
            # if not _NAMclientcore.INTERACT:
            #     connect.send_ctl_answer(ctl_conn, answer)
            #     connect.close_ctl_conn(ctl_conn)
            # else:
            #     if answer != "": print(answer)

    @staticmethod
    def direct_interaction():
        command = _NAMclientcore.get_input()
        if command == None or command == "": return
        return _NAMclientcore.serve_command(command)

    @staticmethod
    def ctl_interaction(ctl_conn):
        command = _NAMclientcore.get_input(ctl_conn)
        if command == None or command == "": return
        return _NAMclientcore.serve_command(command, ctl_conn)

    @staticmethod
    def serve_command(command_string, ctl_conn = None):
        if command_string[0] == "-":
            command = _NAMclientcore.split_command(command_string)
            if command == None:
                _NAMclientcore.send_output("Wrong command, try help", ctl_conn)
                return
            ctl_command_func = getattr(_NAMclientcore, _NAMclientcore.commads_dict[command])
            return ctl_command_func(ctl_conn)
        else:
            return connect.send_data(datastruct.to_dict(datastruct.AIrequest(command_string)))

    @staticmethod
    def split_command(command):
        command_list = command.split(" ")
        command_list.pop(0)
        if len(command_list) < 1: return None
        if command_list[0] in _NAMclientcore.commads_dict: return command_list[0]
        if " ".join(command_list[0:2]) in _NAMclientcore.commads_dict: return " ".join(command_list[0:2])
        return None



    @staticmethod
    def show_help(ctl_conn = None):
        _NAMclientcore.send_output("""
change model - change model for ai
delete con - delete context
file <filename> <file2name> <...> text of your request - include file contents to request
save - save all settings
info - show all info
recon - reconnect to server
stop - stop client
help - show this info""", ctl_conn)

    @staticmethod
    def stop_all(ctl_conn = None):
        _NAMclientcore.send_output("nam server is stopping...", ctl_conn)
        _NAMclientcore.stop_event.set()

    @staticmethod
    def reconnect_to_srv(ctl_conn = None):
        _NAMclientcore.send_output("reconnecting to the server...", ctl_conn)
        _NAMclientcore.reconnect_event.set()

    @staticmethod
    def change_model(ctl_conn = None):
        model = _NAMclientcore.get_input("ai_model (gpt_35_turbo / gpt_35_long / gpt_4 / gpt_4_turbo): ", ctl_conn)
        if model == None: return
        _NAMclientcore.settings.model = datastruct.AImodels(model)
        return connect.send_data(datastruct.to_dict(_NAMclientcore.settings))

    @staticmethod
    def save_all_settings(ctl_conn = None):
        dload.save_json(_NAMclientcore.auth_json, datastruct.to_dict(_NAMclientcore.user))
        dload.yaml_change_single(_NAMclientcore.conf_yaml, ["ai_settings","model"], _NAMclientcore.settings.model.value)

    @staticmethod
    def show_info(ctl_conn = None):
        if _NAMclientcore.reconnect_event.is_set():
            _NAMclientcore.send_output("client is trying to reconnect...", ctl_conn)
        else:
            _NAMclientcore.send_output(f"logged in as {_NAMclientcore.user.name}", ctl_conn)
            _NAMclientcore.send_output(f"current model: {_NAMclientcore.settings.model.value}", ctl_conn)

    @staticmethod
    def delete_context(ctl_conn = None):
        return connect.send_data(datastruct.to_dict(datastruct.NAMcommand(datastruct.NAMCtype.ContextReset)))

def main():
    _NAMclientcore.start_core()

main()
