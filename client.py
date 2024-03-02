
from socket import *
from time import sleep
import sys, os, re, threading, tqdm

def login_func_input():
    userName = input("Username: ")
    userPassword = input("Password: ")
    return f"login {userName} {userPassword}"

sever_host = sys.argv[1]
sever_port = int(sys.argv[2])
udp_port = int(sys.argv[3])
sever_address = (sever_host, sever_port)


clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect(sever_address)

#udp_send function
def send(address, username, filename):
    print("-"*20)
    SEPARATOR = "<SEPARATOR>"
    host, port = address
    Buffersize = 4096 * 10
    filename = filename
    name = username
    file_size = os.path.getsize(filename)
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect((host, port))
    s.send(f'{filename}{SEPARATOR}{name}{SEPARATOR}{file_size}'.encode('utf-8'))
    progress = tqdm.tqdm(range(file_size), f"Sending====={filename}", unit='B', unit_divisor=1024)
    with open(filename, 'rb') as f:
        for _ in progress:
            bytes_read = f.read(Buffersize)
            if not bytes_read:
                s.sendall('file_download_exit'.encode('utf-8'))
                break
            s.sendall(bytes_read)
            progress.update(len(bytes_read))
            sleep(0.001)
    print("-"*20)
    print("DONE!")
    print("Press any key to return to the menu!")
    print("-" * 20)
    s.close()

#udp_receive function
def recvived(address, port):
    SEPARATOR = '<SEPARATOR>'
    Buffersize = 4096 * 10

    while True:

        print("-" * 20)

        udp_socket = socket(AF_INET, SOCK_DGRAM)
        udp_socket.bind((address, port))
        recv_data = udp_socket.recvfrom(Buffersize)
        recv_file_info = recv_data[0].decode('utf-8')  # 存储接收到的数据,文件名

        c_address = recv_data[1]  # 存储客户的地址信息
        # 打印客户端ip
        filename, name, file_size = recv_file_info.split(SEPARATOR)
        filename = os.path.basename(filename)
        file_size = int(file_size)
        progress = tqdm.tqdm(range(file_size), f'Receive {filename}', unit='B', unit_divisor=1024, unit_scale=True)
        with open(f'{name}_' + filename, 'wb') as f:
            for _ in progress:
                bytes_read = udp_socket.recv(Buffersize)
                if bytes_read == b'file_download_exit':
                    break
                f.write(bytes_read)
                progress.update(len(bytes_read))
        print("-"*20)
        print("DONE")
        print("Press any key to return to the menu!")
        udp_socket.close()


# login block
while True:
    a = login_func_input()
    msg = a + f" {udp_port}"

    clientSocket.sendall(msg.encode("utf-8"))
    recvData = clientSocket.recv(1024).decode("utf-8")

    if recvData == "[login] 1":
        username = msg.split()[0]
        print("Welcome to Toom!")

        break
    elif recvData == "[login] 2":
        print("Invalid Password. Please try again")
        continue
    elif recvData == "[login] 3":
        print("Your account is blocked due to multiple login failures. Please try again later")
        continue

#UDP Thrad start
t = threading.Thread(target=recvived, args=("127.0.0.1", udp_port))
t.start()

#main function
while True:
    m = input(f"Enter one of the following commands (BCM, ATU, SRB, SRM, RDM, OUT, UPD): ")
    msg = m.split()
    if len(msg) == 1:
        if msg[0] == "OUT":
            clientSocket.sendall(msg[0].encode("utf-8"))
            username = clientSocket.recv(1024).decode("utf-8")
            print(f"Good Bye {username}")
            break
        if msg[0] == "ATU":
            clientSocket.sendall(msg[0].encode("utf-8"))
            while True:
                recvData = clientSocket.recv(1024).decode("utf-8")
                if recvData.endswith("end"):
                    print(recvData[0:-3])
                    break
                print(recvData)
    elif msg[0] == "BCM":
        clientSocket.sendall(m.encode("utf-8"))
        recvData = clientSocket.recv(1024).decode("utf-8").split(";")
        print(f"Broadcast message, #{recvData[0]} broadcast at {recvData[1]}")
    elif msg[0] == "SRB":
        room_num = 1
        SRB_msg = m
        flag_a = ''
        flag_b = False
        name = ""
        for i in range(1, len(msg)):
            name += f"{msg[i]} "
        clientSocket.sendall(m.encode("utf-8"))
        flag_a, current_user, room_num = clientSocket.recv(1024).decode("utf-8").split()

        if flag_a == "True":
            print(f"Separate chat room has been created, room ID: {room_num}, users in this room: {name} {current_user}")
        elif flag_a == "False":
            print(f"Your provided usernames are offline")
        elif flag_a == "False1":
            print(f"a separate room (ID: {room_num}) already created for these users")

    elif len(msg) == 3 and msg[0] == "SRM":

        clientSocket.sendall(f"{m}".encode("utf-8"))
        Data = clientSocket.recv(1024).decode("utf-8").split()
        if Data[0] != "TrueR":
            print(f"The separate room does not exist")
        else:
            clientSocket.sendall(f"{m}".encode("utf-8"))
            recvData = clientSocket.recv(1024).decode("utf-8").split()
            if recvData[0] == "True":
                print(f"{recvData[4]} issued a message in separate room [{msg[1]}]: {recvData[5]} at {recvData[2]}")

            else:
                print(f"You are not in this separate room chat")


    elif len(msg) == 4 and msg[0] == "RDM":
        clientSocket.sendall(f"{m}".encode("utf-8"))
        while True:
            Data = clientSocket.recv(1024).decode("utf-8")
            recvData = Data.split()
            if recvData[0] == "s":
                print(f"Message in separate rooms since {recvData[1]} {recvData[2]} "
                      f"room-{recvData[3]}: {recvData[4]}")
            if recvData[0] == "b":
                print(f"Broadcast Message issued by {recvData[1]} "
                      f"at {recvData[2]} {recvData[3]} : {recvData[4]}")
            if recvData[0] == "End":
                break

    elif len(msg) == 3 and msg[0] == "UPD":
        username, filename = msg[1:]
        clientSocket.sendall(f"{m}".encode("utf-8"))
        recvData = clientSocket.recv(1024).decode("utf-8").split()
        if recvData[0] == "offline":
            print(f"{username} is offline")
            print()
        else:
            if os.path.exists(filename):
                recvname, recvport = recvData[1:]
                address = ("127.0.0.1", int(recvData[2]))
                t1 = threading.Thread(target=send, args=(address, username, filename))
                t1.start()

    else:
        print(f"Error.  command!")

clientSocket.close()

