######################################################################################
##                                                                                  ##
##                                  client core                                     ##
##                                                                                  ##
######################################################################################


#####   usage:

# client can be started in interact or backgroud mode
# interact mode occupies terminal and needed for tests
# background mode IS NOT SUPPORTED yet (any lines of codes related to unix named sockets are unstable from previous versions)

# arguments: python3 main.py <interact> <configs_path>
# if no <interact> specified, the client starts in the interact mode
# if no <configs_path> specified, the client looking for configs in current folder

# to start client in interact mode use `python3 main.py interact .`

# any written text is sent to the server, except text which starts with sign `-`
# to execute any command try `- command` for ex: `- help`


#####   client insides:

# all work with sockets delegated to intapi/connect.py
# all work with files delegated to dataload/dload.py
# all datastructures used in core located in datastruct.py

# conf_keys dict used to check conf.yaml correctness
# commads_dict used to execute related to client commands functions by their name
# for ex: to add command `- show something` to client, you need to add "show something":"show_something"
# to commads_dict, where show_something is actual name of _NAMclientcore function

# _NAMclientcore uses NAMEtype (NAM execution type) enum to take care of functions execute codes.
# there are other execution codes for other modules, like intapi.connect.py
# they are converted into NAMEtype in related functions

# _NAMclientcore uses NAMDtype as primary unit of transferring data

# responses_thread is thread for receiving data from server in background, so
# user can call commands while waiting for response of ai
# test_conn_thread is thread for testing connection in background

# stop_event to stop client
# reconnect_event to start reconnect process

# lock_srv_in_out() and free_srv_in_out() used to make shure
# that no other thread is listening for or sending data to the server
# when it needed

import datastruct
import bcrypt
import time
from dataload import dload
from intapi import connect
from threading import Thread
from threading import Event
import copy
import signal
import setproctitle
import sys

class _NAMclientcore(object):

    salt            =   b'$2b$12$ET4oX.YJCrU9OX92KWW2Ku'
    conf_yaml       =   "conf.yaml"
    auth_json       =   "auth.json"
    conf_is_valid   =   False
    user            =   None            # auth data
    settings        =   None            # session settings (for now just ai model)
    current_output_unix_socket = None   # unix named socket used in background mode (NOT WORKING)

    input_thread            =   None    # inputs from user
    responses_thread        =   None    # responses from server
    test_conn_thread        =   None    # test connection between client and server
    stop_event              =   Event() # stop client event
    reconnect_event         =   Event() # event to start reconnect process
    srv_input_lock_event    =   Event() # move responses_thread to idle state
    srv_output_lock_event   =   Event() # move test_conn_thread to idle state
    responses_thread_idle   =   False   # used to determine if responses_thread reached idle state
    test_conn_thread_idle   =   False   # used to determine if test_conn_thread reached idle state

    # list used to check conf.yaml correctness
    conf_keys = ["ai_settings", "model", "nam_client", "connect", "encoding", "server_ip", "server_port", "unix_socket_path"]

    # dict for matching command and corresponding _NAMclientcore function
    commads_dict = {"change model": "change_model", "delete con":"delete_context", "info":"show_info",
                    "save":"save_all_settings", "stop":"stop_all", "recon":"reconnect_to_srv", "relog":"relogin_to_srv", "help":"show_help"}

    INTERACT = True # interact or background mode


########################## System functions ##########################

    @staticmethod
    def start_core():
        signal.signal(signal.SIGTERM, _NAMclientcore.sigterm_handler)   # handle SIGTERM signal
        setproctitle.setproctitle('nam_client_python')
        if _NAMclientcore.solve_cli_args() == datastruct.NAMEtype.IntFail: raise Exception("Wrong arguments or argument positions!")
        if _NAMclientcore.test_conf_file(_NAMclientcore.conf_yaml, _NAMclientcore.conf_keys) == False:
            raise Exception("conf.yaml file is invalid!")
        if _NAMclientcore.init_connect() == datastruct.NAMEtype.InitConnFail: raise Exception("Failed to start listening sock! (maybe already running)")
        _NAMclientcore.user = _NAMclientcore.load_auth_data()
        _NAMclientcore.settings = _NAMclientcore.load_ai_settings()
        excode = _NAMclientcore.connect_to_srv()
        match excode:
            case datastruct.NAMEtype.SrvConFail:
                _NAMclientcore.send_output("Server is not reachable")
            case datastruct.NAMEtype.Deny:
                _NAMclientcore.send_output("Wrong username or password. To change user use - relog or try - help")
            case datastruct.NAMEtype.IntFail:
                _NAMclientcore.send_output("Strange data in user info or settings info. Check model in conf.yaml. Try changing user or model by commands in - help")
            case datastruct.NAMEtype.SrvFail:
                _NAMclientcore.send_output("Unexpected error on server")
        if excode != datastruct.NAMEtype.Success:
            _NAMclientcore.send_output("Failed to connect to server")
            _NAMclientcore.reconnect_to_srv()
        _NAMclientcore.responses_thread = Thread(target=_NAMclientcore.serve_responses, args=[])
        _NAMclientcore.responses_thread.start()
        _NAMclientcore.input_thread = Thread(target=_NAMclientcore.serve_input, args=[])
        _NAMclientcore.input_thread.start()
        _NAMclientcore.test_conn_thread = Thread(target=_NAMclientcore.test_connection_async, args=[])
        _NAMclientcore.test_conn_thread.start()
        _NAMclientcore.serve_client()

    @staticmethod
    def solve_cli_args():
        if "interact" in sys.argv:
            _NAMclientcore.INTERACT = True
        if len(sys.argv) == 2:
            if str(sys.argv[1]) != "interact":
                if dload.test_file(str(sys.argv[1])+"/conf.yaml"):
                    _NAMclientcore.conf_yaml = str(sys.argv[1])+"/conf.yaml"
                    _NAMclientcore.auth_json = str(sys.argv[1])+"/auth.json"
                    return datastruct.NAMEtype.Success
        elif len(sys.argv) == 3:
            if str(sys.argv[2]) != "interact":
                if dload.test_file(str(sys.argv[2])+"/conf.yaml"):
                    _NAMclientcore.conf_yaml = str(sys.argv[2])+"/conf.yaml"
                    _NAMclientcore.auth_json = str(sys.argv[2])+"/auth.json"
                    return datastruct.NAMEtype.Success
        return datastruct.NAMEtype.IntFail

    @staticmethod
    def check_key(dictionary, key): # check if key in multidimensional dictionary
        for dict_key in dictionary:
            if dict_key == key:
                return True
            if isinstance(dictionary[dict_key], dict):
                if _NAMclientcore.check_key(dictionary[dict_key], key):
                    return True
        return False

    @staticmethod
    def test_conf_file(path, args : list):
        if not dload.test_file(path): return False
        conf_dict = dload.load_yaml(path)
        all_keys_codes = []
        for arg in args:
            all_keys_codes.append(_NAMclientcore.check_key(conf_dict, arg))
        if False not in all_keys_codes:
            return True
        else : return False

    @staticmethod
    def send_output(data): # send output to user depending on running mode (print if interact and unix named socket if bg)
        if data == None or data == "": return datastruct.NAMEtype.IntFail
        if _NAMclientcore.current_output_unix_socket == None:
            print(data)
            return datastruct.NAMEtype.Success
        else:
            sendcode = connect.send_ctl_answer(_NAMclientcore.current_output_unix_socket, data)
            match sendcode:
                case connect.NAMconcode.Timeout:
                    return datastruct.NAMEtype.ConTimeOut
                case connect.NAMconcode.Fail:
                    return datastruct.NAMEtype.IntConFail
                case connect.NAMconcode.Success:
                    return datastruct.NAMEtype.Success

    @staticmethod
    def get_input(prompt = "nam> "):  # get input from user depending on running mode (input if interact and unix named socket if bg)
        if prompt == None: return datastruct.NAMEtype.IntFail
        if _NAMclientcore.current_output_unix_socket == None:
            print(prompt, end="")
            usr_input = input()
            return usr_input
        else:
            sendcode = _NAMclientcore.send_output(f"IEN {prompt}")
            if sendcode != datastruct.NAMEtype.Success: return sendcode
            usr_input = connect.get_ctl_command(_NAMclientcore.current_output_unix_socket, 4096)
            match usr_input:
                case connect.NAMconcode.Timeout:
                    return datastruct.NAMEtype.ConTimeOut
                case connect.NAMconcode.Fail:
                    return datastruct.NAMEtype.IntConFail
                case "":
                    return datastruct.NAMEtype.IntFail
                case _:
                    return usr_input

    @staticmethod
    def send_srv_data(data): # send data to nam server (remember to lock_srv_in_out and free_srv_in_out if needed)
        if datastruct.to_dict(data) == None: return datastruct.NAMEtype.IntFail
        sendcode = connect.send_data(datastruct.to_dict(data))
        match sendcode:
            case connect.NAMconcode.Timeout:
                return datastruct.NAMEtype.ConTimeOut
            case connect.NAMconcode.Fail:
                return datastruct.NAMEtype.SrvConFail
            case connect.NAMconcode.Success:
                return datastruct.NAMEtype.Success

    @staticmethod
    def connection_is_alive(): # check if connection to srv is alive
        excode = _NAMclientcore.send_srv_data(datastruct.NAMcommand(datastruct.NAMCtype.TestConn))
        if excode == datastruct.NAMEtype.SrvConFail:
            return False
        return True

    @staticmethod
    def get_srv_data(nothing_extra=False): # get data from nam srv (remember to lock_srv_in_out and free_srv_in_out if needed)
        data = connect.get_data(4096)
        if type(data) != connect.NAMconcode:
            obj = datastruct.from_dict(data)
            if obj != None:
                if obj.type == datastruct.NAMDtype.NAMexcode:
                    match obj.code:
                        case datastruct.NAMEtype.Success:
                            return datastruct.NAMEtype.Success
                        case datastruct.NAMEtype.Deny:
                            return datastruct.NAMEtype.Deny
                        case datastruct.NAMEtype.ClientFail:
                            return datastruct.NAMEtype.IntFail
                        case _:
                            return datastruct.NAMEtype.SrvFail
                elif obj.type == datastruct.NAMDtype.NAMcommand:
                    if obj.command == datastruct.NAMCtype.TestConn and nothing_extra:
                        print("recursive call")
                        return _NAMclientcore.get_srv_data(nothing_extra)
                    else: return obj
                else: return obj
            else: return datastruct.NAMEtype.SrvFail
        match data:
            case connect.NAMconcode.Timeout:
                return datastruct.NAMEtype.ConTimeOut
            case connect.NAMconcode.Fail:
                return datastruct.NAMEtype.SrvConFail
            case connect.NAMconcode.JsonFail:
                return datastruct.NAMEtype.SrvFail

    @staticmethod
    def lock_srv_input(): # wait while responses_thread isn't in idle state
        if _NAMclientcore.responses_thread == None: return True
        _NAMclientcore.srv_input_lock_event.set()
        while not _NAMclientcore.responses_thread_idle:
            if _NAMclientcore.stop_event.is_set(): break
        return True

    @staticmethod
    def free_srv_input():
        if _NAMclientcore.responses_thread == None: return True
        _NAMclientcore.srv_input_lock_event.clear()
        while _NAMclientcore.responses_thread_idle:
            if _NAMclientcore.stop_event.is_set(): break
        return True

    @staticmethod
    def lock_srv_output(): # wait while test_conn_thread isn't in idle state
        if _NAMclientcore.test_conn_thread == None: return True
        _NAMclientcore.srv_output_lock_event.set()
        while not _NAMclientcore.test_conn_thread_idle:
            if _NAMclientcore.stop_event.is_set(): break
        return True

    @staticmethod
    def free_srv_output():
        if _NAMclientcore.test_conn_thread == None: return True
        _NAMclientcore.srv_output_lock_event.clear()
        while _NAMclientcore.test_conn_thread_idle:
            if _NAMclientcore.stop_event.is_set(): break
        return True

    @staticmethod
    def lock_srv_in_out():
        _NAMclientcore.lock_srv_input()
        _NAMclientcore.lock_srv_output()

    @staticmethod
    def free_srv_in_out():
        _NAMclientcore.free_srv_input()
        _NAMclientcore.free_srv_output()

    @staticmethod
    def sigterm_handler(signal, frame):
        print('Received SIGTERM. Exiting gracefully...')
        _NAMclientcore.stop_event.set()

    @staticmethod
    def init_connect():
        connect_settings = dload.load_yaml(_NAMclientcore.conf_yaml)["nam_client"]["connect"]
        if connect.init_client(connect_settings, _NAMclientcore.INTERACT) == connect.NAMconcode.Success:
            return datastruct.NAMEtype.Success
        else: return datastruct.NAMEtype.InitConnFail

    @staticmethod
    def connect_to_srv():
        if datastruct.to_dict(_NAMclientcore.user) == None or datastruct.to_dict(_NAMclientcore.settings) == None:
            return datastruct.NAMEtype.IntFail
        else:
            _NAMclientcore.lock_srv_in_out()
            sendcode = connect.connect_to_srv(auth_data=datastruct.to_dict(_NAMclientcore.user), settings=datastruct.to_dict(_NAMclientcore.settings))
            if sendcode == connect.NAMconcode.OldSock:
                _NAMclientcore.free_srv_in_out()
                return datastruct.NAMEtype.SrvFail
            if sendcode != connect.NAMconcode.Success:
                _NAMclientcore.free_srv_in_out()
                return datastruct.NAMEtype.SrvConFail
            concode = _NAMclientcore.get_srv_data(nothing_extra=True)
            _NAMclientcore.free_srv_in_out()
            if concode == datastruct.NAMEtype.ConTimeOut or concode == datastruct.NAMEtype.SrvConFail:
                return datastruct.NAMEtype.SrvConFail
            return concode

    @staticmethod
    def encode_passwd(passwd):
        return bcrypt.hashpw(passwd, _NAMclientcore.salt).decode()

    @staticmethod
    def load_auth_data():
        auth = dload.load_json(_NAMclientcore.auth_json)
        if auth != None:
            usr = datastruct.from_dict(auth)
            if usr != None: return usr
        while True:
            _NAMclientcore.send_output("enter auth data:")
            user_name = _NAMclientcore.get_input("user_name: ")
            user_pass = _NAMclientcore.get_input(f"password for user {user_name}: ")
            if user_name == datastruct.NAMEtype.ConTimeOut or user_pass == datastruct.NAMEtype.ConTimeOut: continue
            if user_name != datastruct.NAMEtype.IntConFail and user_name != "" and user_pass != datastruct.NAMEtype.IntConFail and user_pass != "":
                break
        _NAMclientcore.send_output("to save auth data, try '- save' or '- help' for more info")
        return datastruct.NAMuser(name=user_name, pass_hash=_NAMclientcore.encode_passwd(user_pass.encode(encoding=connect.get_encoding())))

    @staticmethod
    def load_ai_settings():
        ai_settings = dload.load_yaml(_NAMclientcore.conf_yaml)["ai_settings"]
        return datastruct.NAMSesSettings(model=datastruct.AImodels(ai_settings["model"]))


########################## Threads and main loop ##########################

    @staticmethod
    def serve_responses():
        while True:
            time.sleep(0.2)
            if _NAMclientcore.stop_event.is_set(): break
            if _NAMclientcore.srv_input_lock_event.is_set():
                _NAMclientcore.responses_thread_idle = True
                continue
            _NAMclientcore.responses_thread_idle = False
            if _NAMclientcore.reconnect_event.is_set(): continue
            response = _NAMclientcore.get_srv_data()
            if type(response) != datastruct.NAMEtype:
                if response.type == datastruct.NAMDtype.AIresponse:
                    _NAMclientcore.send_output(response.message)
            else:
                if response == datastruct.NAMEtype.SrvFail:
                    _NAMclientcore.send_output("Unexpected error on server")

    @staticmethod
    def serve_input():
        while True:
            if _NAMclientcore.stop_event.is_set(): break
            if _NAMclientcore.INTERACT: excode = _NAMclientcore.direct_interaction()
            else:
                _NAMclientcore.current_output_unix_socket = connect.get_ctl_connect()
                excode = _NAMclientcore.ctl_interaction()
                _NAMclientcore.send_output("END")
                connect.close_ctl_conn(_NAMclientcore.current_output_unix_socket)
                _NAMclientcore.current_output_unix_socket = None
            if excode != datastruct.NAMEtype.Success: _NAMclientcore.send_output("Error. The command was not executed")
            match excode:
                case datastruct.NAMEtype.ConTimeOut:
                    _NAMclientcore.send_output("Connection to the srv timed out")
                case datastruct.NAMEtype.SrvConFail:
                    _NAMclientcore.send_output("Connection is faulty")
                case datastruct.NAMEtype.SrvFail:
                    _NAMclientcore.send_output("Unexpected error on server")

    @staticmethod
    def test_connection_async():
        while True:
            if _NAMclientcore.stop_event.is_set(): break
            if _NAMclientcore.srv_output_lock_event.is_set():
                _NAMclientcore.test_conn_thread_idle = True
                continue
            _NAMclientcore.test_conn_thread_idle = False
            if _NAMclientcore.reconnect_event.is_set(): continue
            time.sleep(1)
            if not _NAMclientcore.connection_is_alive() and not _NAMclientcore.reconnect_event.is_set():
                    _NAMclientcore.reconnect_to_srv()
            for i in range(0, 10):
                if _NAMclientcore.stop_event.is_set(): break
                if _NAMclientcore.srv_output_lock_event.is_set(): break
                time.sleep(2)

    @staticmethod
    def serve_client(): # main loop
        sock_was_connected = True
        while True:
            time.sleep(2)
            if _NAMclientcore.stop_event.is_set():
                _NAMclientcore.input_thread.join()
                _NAMclientcore.responses_thread.join()
                _NAMclientcore.test_conn_thread.join()
                connect.close_conn()
                if not _NAMclientcore.INTERACT: connect.close_local_sock()
                print("done")
                break
            if _NAMclientcore.reconnect_event.is_set():
                if sock_was_connected == True:
                    connect.close_conn()
                    connect.open_new_sock()
                    sock_was_connected = False
                    time.sleep(1)
                excode = _NAMclientcore.connect_to_srv()
                if excode == datastruct.NAMEtype.Success:
                    _NAMclientcore.reconnect_event.clear()
                    sock_was_connected = True
                    _NAMclientcore.send_output("reconnected")
                if excode == datastruct.NAMEtype.Deny or excode == datastruct.NAMEtype.SrvFail or excode == datastruct.NAMEtype.IntFail:
                    sock_was_connected = True
                    print("rebinding socket")


########################## Serve inputed command ##########################

    @staticmethod
    def direct_interaction():
        command = _NAMclientcore.get_input()
        if type(command) == datastruct.NAMEtype: return command
        return _NAMclientcore.serve_command(command)

    @staticmethod
    def ctl_interaction():
        command = _NAMclientcore.get_input()
        if type(command) == datastruct.NAMEtype: return command
        return _NAMclientcore.serve_command(command)

    @staticmethod
    def serve_command(command_string):
        if command_string == "": return datastruct.NAMEtype.Success
        if command_string[0] == "-":
            command = _NAMclientcore.split_command(command_string)
            if command == None:
                _NAMclientcore.send_output("Wrong command, try help")
                return datastruct.NAMEtype.IntFail
            ctl_command_func = getattr(_NAMclientcore, _NAMclientcore.commads_dict[command])
            return ctl_command_func()
        else:
            if _NAMclientcore.reconnect_event.is_set():
                _NAMclientcore.send_output("you can't ask questions for now. Client is reconnecting...")
                return datastruct.NAMEtype.IntFail
            else: return _NAMclientcore.send_srv_data(datastruct.AIrequest(command_string))

    @staticmethod
    def split_command(command):
        command_list = command.split(" ")
        command_list.pop(0)
        if len(command_list) < 1: return None
        if command_list[0] in _NAMclientcore.commads_dict: return command_list[0]
        if " ".join(command_list[0:2]) in _NAMclientcore.commads_dict: return " ".join(command_list[0:2])
        return None


########################## Client commands implementations ##########################

    @staticmethod
    def show_help():
        _NAMclientcore.send_output("""
change model - change model for ai
delete con - delete context
file <filename> <file2name> <...> text of your request - include file contents to request
save - save all settings
info - show all info
recon - reconnect to server
relog - relogin with new user info to srv
stop - stop client
help - show this info""")
        return datastruct.NAMEtype.Success

    @staticmethod
    def stop_all():
        _NAMclientcore.send_output("nam client is stopping...")
        _NAMclientcore.stop_event.set()
        return datastruct.NAMEtype.Success

    @staticmethod
    def reconnect_to_srv():
        _NAMclientcore.send_output("reconnecting to the server...")
        _NAMclientcore.reconnect_event.set()
        return datastruct.NAMEtype.Success

    @staticmethod
    def relogin_to_srv():
        while True:
            _NAMclientcore.send_output("enter auth data:")
            user_name = _NAMclientcore.get_input("user_name: ")
            user_pass = _NAMclientcore.get_input(f"password for user {user_name}: ")
            if user_name == datastruct.NAMEtype.ConTimeOut or user_pass == datastruct.NAMEtype.ConTimeOut: continue
            if user_name != datastruct.NAMEtype.IntConFail and user_name != "" and user_pass != datastruct.NAMEtype.IntConFail and user_pass != "":
                break
        _NAMclientcore.send_output("to save auth data, try '- save' or '- help' for more info")
        _NAMclientcore.user = datastruct.NAMuser(name=user_name, pass_hash=_NAMclientcore.encode_passwd(user_pass.encode(encoding=connect.get_encoding())))
        return _NAMclientcore.reconnect_to_srv()

    @staticmethod
    def change_model():
        new_set = copy.deepcopy(_NAMclientcore.settings)
        while True:
            model = _NAMclientcore.get_input("ai_model (gpt_35_turbo / gpt_35_long / gpt_4 / gpt_4_turbo): ")
            if type(model) != datastruct.NAMEtype:
                if model in [aimodel.value for aimodel in datastruct.AImodels]:
                    new_set.model = datastruct.AImodels(model)
                    break
                else:
                    _NAMclientcore.send_output("no such model available")
                    return datastruct.NAMEtype.IntFail
        _NAMclientcore.lock_srv_in_out()
        sendcode = _NAMclientcore.send_srv_data(new_set)
        if sendcode != datastruct.NAMEtype.Success:
            _NAMclientcore.free_srv_in_out()
            return sendcode
        excode = _NAMclientcore.get_srv_data(nothing_extra=True)
        _NAMclientcore.free_srv_in_out()
        if excode == datastruct.NAMEtype.Success:
            _NAMclientcore.settings = new_set
            return excode
        else: return excode

    @staticmethod
    def save_all_settings():
        sc1 = dload.save_json(_NAMclientcore.auth_json, datastruct.to_dict(_NAMclientcore.user))
        sc2 = dload.yaml_change_single(_NAMclientcore.conf_yaml, ["ai_settings","model"], _NAMclientcore.settings.model.value)
        if sc1 and sc2: return datastruct.NAMEtype.Success
        else: return datastruct.NAMEtype.IntFail

    @staticmethod
    def show_info():
        if _NAMclientcore.reconnect_event.is_set():
            _NAMclientcore.send_output("client is trying to reconnect...")
        else:
            _NAMclientcore.send_output(f"logged in as {_NAMclientcore.user.name}")
            _NAMclientcore.send_output(f"current model: {_NAMclientcore.settings.model.value}")
        return datastruct.NAMEtype.Success

    @staticmethod
    def delete_context():
        _NAMclientcore.lock_srv_in_out()
        sendcode = _NAMclientcore.send_srv_data(datastruct.NAMcommand(datastruct.NAMCtype.ContextReset))
        if sendcode != datastruct.NAMEtype.Success:
            _NAMclientcore.free_srv_in_out()
            return sendcode
        excode = _NAMclientcore.get_srv_data(nothing_extra=True)
        _NAMclientcore.free_srv_in_out()
        return excode



def main():
    _NAMclientcore.start_core()

if __name__ == "__main__":
    main()
