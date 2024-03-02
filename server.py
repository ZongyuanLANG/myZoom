from datetime import datetime
from socket import *
from threading import Thread
import sys, re, time, os
from typing import Dict

if len(sys.argv) != 3:
    print(f"\n==== Error usage, python3 server.py server_port number_of_consecutive_failed_attempts ====\n")
    exit(0)

server_host = "127.0.0.1"
server_port = int(sys.argv[1])
login_attempts = int(sys.argv[2])
server_address = (server_host, server_port)

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(server_address)

user_try_times_flag = dict()
user_password_dict = dict()
active_user = {}
userlog = []
message_num = 1
user_log_num = 1
SRM_num = 1
room = {}
room_num = 1
rooms = []
udp = {}

# Get username and password
with open("credentials.txt", "rt") as f:
    content = f.read().split()
    for i in range(0, len(content) - 1, 2):
        user_password_dict[content[i]] = content[i + 1]
        user_try_times_flag[content[i]] = [0, True]


class MyThread(Thread):

    def __init__(self, clientAddress, clientSocket):
        Thread.__init__(self)
        self.clientSocket = clientSocket
        self.clientAddress = clientAddress
        self.user_locked_time = dict()
        self.clientAlive = False
        self.name = ""

        global user_password_dict
        global user_try_times_flag
        global active_user
        global login_attempts
        global message_num
        global room_num
        global room
        global user_log_num
        global rooms
        global SRM_num
        global udp
        print(f"=== New connection created from: {clientAddress}")
        self.clientAlive = True

    def run(self):
        global message_num, room_num
        while self.clientAlive:
            recv_data = self.clientSocket.recv(1024).decode("utf-8").split()
            # Authentication
            if len(recv_data) == 4 and recv_data[0] != "SRB" and recv_data[0] != "SRM" and recv_data[0] != "RDM":
                name = recv_data[1]
                password = recv_data[2]
                udp_port = recv_data[3]
                if user_password_dict[name] == password:
                    if not user_try_times_flag[name][1]:
                        self.process_login_3()
                    else:
                        self.name = name
                        t = str(datetime.now())[0: -7]
                        active_user[name] = t
                        udp[name] = udp_port
                        if not os.path.getsize("userlog.txt"):
                            user_log_num = 1
                        else:
                            with open("userlog.txt", "rt") as f:
                                content = f.readlines()
                                user_log_num = int(content[len(content) - 1][0]) + 1
                        msg = f"{user_log_num}; {t}; {name}"
                        with open("userlog.txt", 'a') as file:
                            file.write(msg + '\n')
                        self.process_login_1()
                elif user_password_dict[name] != password and user_try_times_flag[name][1]:
                    self.process_login_2()
                    user_try_times_flag[name][0] += 1
                    if user_try_times_flag[name][0] >= int(login_attempts) and user_try_times_flag[name][1]:
                        user_try_times_flag[name][1] = False
                        user_try_times_flag[name][0] = 0
                        self.user_locked_time[name] = time.time()
                        print(self.user_locked_time[name])
                elif user_password_dict[name] != password and not user_try_times_flag[name][1]:
                    self.process_login_3()

                    if time.time() - self.user_locked_time[name] > 5:
                        user_try_times_flag[name][1] = True

            elif len(recv_data) == 1 and recv_data[0] != "InRoom":
                # Out fuction
                if recv_data[0] == "OUT":
                    c = []
                    flag = False
                    with open("userlog.txt", "rt") as file:
                        for line in file.readlines():
                            line = line.strip()
                            line = line.split(";")
                            if len(line) > 2:
                                if line[2] == f" {self.name}":
                                    flag = True
                                    continue
                                elif flag:
                                    line[0] = f"{int(line[0]) - 1}"
                                    c.append(line)
                                else:
                                    c.append(line)
                    self.clientSocket.sendall(f"{self.name}".encode("utf-8"))
                    with open("userlog.txt", "w") as f:
                        for i in c:
                            f.write(f"{i[0]}; {i[1]}; {i[2]}\n")
                    del active_user[self.name]
                    print("-" * 20)
                    print(f"Good Bye! {self.name}")
                    print("-" * 20)
                # ATU function
                if recv_data[0] == "ATU":
                    print("-" * 20)
                    print(f"{self.name} issued ATU command")
                    print("Return messages: ")
                    if len(active_user) > 1:
                        for key, value in active_user.items():
                            if key == f"{self.name}":
                                continue
                            else:
                                msg = f"{key}, active since {value}"
                                print(msg)
                                self.clientSocket.sendall(msg.encode("utf-8"))
                        self.clientSocket.sendall("end".encode("utf-8"))
                    else:
                        print("no other active user")
                        self.clientSocket.sendall("no other active user".encode("utf-8"))
                        self.clientSocket.sendall("end".encode("utf-8"))
                    print("-" * 20)
            # BCM function
            elif len(recv_data) == 2 and recv_data[0] != "SRB":
                if recv_data[0] == "BCM":
                    t = str(datetime.now())[0: -7]
                    if not os.path.getsize("messagelog.txt"):
                        message_num = 1
                    else:
                        with open("messagelog.txt", "rt") as f:
                            content = f.readlines()
                            message_num = int(content[len(content) - 1][0]) + 1
                            print(content[len(content) - 1][0])
                            print(message_num)

                    msg = f"{message_num}; {t}; {self.name}; {recv_data[1]}"
                    self.file_write("messagelog.txt", msg)
                    print("-" * 20)
                    print(f'{self.name} broadcasted BCM #{message_num} "{recv_data[1]}" at {t}.')
                    self.clientSocket.sendall(msg.encode("utf-8"))
                    print("-" * 20)
            # SRB function
            elif len(recv_data) >= 2 and recv_data[0] == "SRB":
                name = ""
                flag = False
                keys = list(active_user.keys())
                for i in range(1, len(recv_data)):
                    name += f"{recv_data[i]} "
                names = name.split()
                names.append(self.name)
                dif = set(names) - set(keys)
                print(dif)
                print(room)
                if len(dif) > 0:
                    self.clientSocket.sendall(f"False {self.name} {room_num}".encode("utf-8"))
                    print("-" * 20)
                    print(f"Your provided usernames are offline")
                    print("-" * 20)
                else:
                    if len(room) == 0:
                        self.clientSocket.sendall(f"True {self.name} {room_num}".encode("utf-8"))
                        room[room_num] = names
                        room_num += 1
                        print("-" * 20)
                        print(f"{self.name} issued SRB command")
                        print(f"Separate chat room has been created, "
                              f"room ID: {room_num - 1}, users in this room: {name} {self.name}")
                        print("-" * 20)
                    else:
                        for key, values in room.items():
                            if len(set(names) - set(values)) > 0:
                                flag = True
                        if flag:
                            self.clientSocket.sendall(f"True {self.name} {room_num}".encode("utf-8"))
                            print("-" * 20)
                            print(f"{self.name} issued SRB command")
                            print(f"Return message: Separate chat room has been created, room ID: {room_num} "
                                  f"users in this room:{name} {self.name}")
                            print("-" * 20)
                            room[room_num] = names
                            room_num += 1
                        else:
                            self.clientSocket.sendall(f"False1 {self.name} {i}".encode("utf-8"))
            # SRM function
            elif len(recv_data) == 3 and recv_data[0] == "SRM":
                t = str(datetime.now())[0:-7]
                if not os.path.getsize("SR_ID_messagelog.txt"):
                    SRM_num = 1
                else:
                      with open("SR_ID_messagelog.txt", "rt") as f:
                        content = f.readlines()
                        SRM_num = int(content[len(content) - 1][0]) + 1

                check_room = recv_data[1]
                if check_room in room.keys():
                    self.clientSocket.sendall("True".encode(("utf-8")))
                else:
                    self.clientSocket.sendall("TrueR".encode(("utf-8")))
                data = self.clientSocket.recv(1024).decode("utf-8").split()
                for key, values in room.items():

                    if str(key) == data[1] and self.name in values:
                        msg1 = f"{SRM_num}; room-{key}; {t}: {self.name}: {data[2]}\n"
                        print("-" * 20)
                        print(f"{self.name} issued a message in separate room {data[1]}: #{msg1}")
                        print("-" * 20)
                        self.clientSocket.sendall(f"True {SRM_num} {t} {self.name} {data[2]}".encode("utf-8"))
                        with open("SR_ID_messageLog.txt", "a") as f:
                            f.write(msg1)
                self.clientSocket.sendall(f"False".encode("utf-8"))
            # RDM function
            elif len(recv_data) == 4 and recv_data[0] == "RDM":
                print("-" * 20)
                print(f"RDM command issued from {self.name}")
                min = recv_data[3][3:5]
                sec = recv_data[3][6:8]
                if recv_data[1] == "b":
                    print(f"Return message ")
                    if not os.path.getsize("messagelog.txt"):
                        print("No message!")
                        print("-" * 20)
                    else:
                        with open("messagelog.txt", 'rt') as f:
                            content = f.readlines()
                            for line in content:
                                m = line.split()[2][3:5]
                                s = line.split()[2][6:8]
                                if int(m) >= int(min):
                                    msg = f"b {line.split()[3]} {line.split()[1]} " \
                                          f"{line.split()[2]} {line.split()[4]} "
                                    print(msg)
                                    self.clientSocket.sendall(msg.encode("utf-8"))
                                    time.sleep(0.1)
                                    print(f"{line.split()[4]}")
                                    print("-" * 20)
                            self.clientSocket.sendall("End".encode("utf-8"))
                if recv_data[1] == "s":
                    print(f"Return message ")
                    if not os.path.getsize("SR_ID_messagelog.txt"):
                        print("No message!")
                        print("-" * 20)
                    else:
                        with open("SR_ID_messagelog.txt", 'rt') as f:
                            content = f.readlines()
                            for line in content:
                                m = line.split()[3][3:5]
                                s = line.split()[3][6:8]
                                if int(m) >= int(min):
                                    msg = f"s {line.split()[2]} {line.split()[3]} {line.split()[1]} {line.split()[5]} "
                                    self.clientSocket.sendall(msg.encode("utf-8"))
                                    time.sleep(0.1)
                                    print(f"{line.split()[5]}")
                                    print("-" * 20)
                            self.clientSocket.sendall("End".encode("utf-8"))
            # UPD funtion
            elif len(recv_data) == 3 and recv_data[0] == "UPD":
                name = recv_data[1]
                print(udp)
                if name in active_user.keys():
                    self.clientSocket.sendall(f"online {name} {udp[name]}".encode("utf-8"))
                else:
                    self.clientSocket.sendall("offline".encode("utf-8"))

    # write message into file
    def file_write(self, file_name, msg):
        with open(file_name, 'a') as file:
            file.write(msg + '\n')

    # logincheck1
    def process_login_1(self):
        self.clientSocket.sendall("[login] 1".encode("utf-8"))

    # logincheck2
    def process_login_2(self):
        self.clientSocket.sendall("[login] 2".encode("utf-8"))

    # logincheck3
    def process_login_3(self):
        self.clientSocket.sendall("[login] 3".encode("utf-8"))


while True:
    serverSocket.listen()
    clientSockt, clientAddress = serverSocket.accept()
    print(clientAddress)
    myThread = MyThread(clientAddress, clientSockt)
    myThread.start()
