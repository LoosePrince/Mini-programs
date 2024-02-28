# 编译exe程序
# Cmd : pyinstaller --onefile
# client.py build

import tkinter as tk
from tkinter import ttk
from threading import Thread
import socket
import time

SERVER_IP = "127.0.0.1"  # 修改为您的服务器IP
SERVER_PORT = 8080  # 修改为您的服务器端口
SECRET_KEY = "your_secret_key"  # 修改为您的密钥

client_socket = None
connected = False

def connect_server():
    global client_socket, connected
    if not connected:
        server_ip = ip_entry.get().strip()
        server_port = port_entry.get().strip()
        secret_key = key_entry.get().strip()

        if server_ip and server_port and secret_key:
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((server_ip, int(server_port)))
                client_socket.setblocking(True)  # 设置为阻塞模式

                # 发送密钥以进行验证
                key = secret_key.encode('utf-8')
                key_header = f"{len(key):<10}".encode('utf-8')
                client_socket.send(key_header + key)

                connected = True
                root.title("简易聊天室 - 已连接")
                connect_button.config(text="断开")
                ip_entry.config(state='readonly')
                port_entry.config(state='readonly')
                key_entry.config(state='readonly')

                # 启动接收消息的线程
                Thread(target=receive_messages_loop, daemon=True).start()
                # 请求在线列表
                request_online_list()
            except Exception as e:
                print("连接失败:", e)
    else:
        disconnect_server()

def request_online_list():
    if client_socket and connected:
        client_socket.send(f"{len('/list'):<10}".encode('utf-8') + "/list".encode('utf-8'))

def disconnect_server():
    global client_socket, connected
    if client_socket:
        client_socket.close()
        client_socket = None
    connected = False
    root.title("简易聊天室")
    connect_button.config(text="连接")
    ip_entry.config(state='normal')
    port_entry.config(state='normal')
    key_entry.config(state='normal')
    online_list.delete(0, tk.END)
    online_count.set(f"已离线")

def send_message(input_entry):
    global client_socket
    if client_socket and connected:
        message = input_entry.get().strip()
        if message:
            input_entry.delete(0, tk.END)  # 清空输入框
            message = message.encode('utf-8')
            message_header = f"{len(message):<10}".encode('utf-8')
            client_socket.send(message_header + message)
            current_time = time.strftime("%H:%M:%S %Y-%m-%d")
            formatted_message = f"{message.decode('utf-8')} : 我 [{current_time}]"
            insert_message(formatted_message, 'right')

online_ids = set()  # 新增：用于跟踪当前在线的用户ID

def receive_messages_loop():
    global client_socket, connected
    while connected:
        try:
            message_header = client_socket.recv(10)
            if not len(message_header):
                print("服务器关闭了连接。")
                break
            message_length = int(message_header.decode('utf-8').strip())
            message = client_socket.recv(message_length).decode('utf-8')

            # 处理特殊格式的消息，更新在线人数
            if message.startswith("当前人数"):
                # 解析在线人数
                _, current_count = message.split()
                online_count.set(f"在线人数: {current_count}")  # 直接更新在线人数显示
                current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                formatted_message = f"[{current_time}] {message}"
                insert_message(formatted_message, 'left')
            elif "加入了房间" in message:
                user_id = message.split(' ')[0]
                #if user_id not in online_ids:  # 避免重复添加
                add_to_online_list(user_id)
                current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                formatted_message = f"[{current_time}] {message}"
                insert_message(formatted_message, 'left')
            elif "离开了房间" in message:
                user_id = message.split(' ')[0]
                if user_id in online_ids:  # 仅当ID存在时移除
                    remove_from_online_list(user_id)
                current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                formatted_message = f"[{current_time}] {message}"
                insert_message(formatted_message, 'left')
            elif message.startswith("{"):
                update_online_list(message)
            else:
                current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                formatted_message = f"[{current_time}] {message}"
                insert_message(formatted_message, 'left')
        except Exception as e:
            print("接收消息时出错:", e)
            break
    disconnect_server()

def add_to_online_list(user_id):
    global online_ids
    online_ids.add(user_id)
    online_list.insert(tk.END, user_id)  # 将用户ID添加到列表中

def remove_from_online_list(user_id):
    global online_ids
    online_ids.remove(user_id)
    # 由于在线列表允许重复ID，删除时需要特别处理
    # 遍历列表，删除第一个匹配的ID
    for i, list_id in enumerate(online_list.get(0, tk.END)):
        if list_id == user_id:
            online_list.delete(i)
            break

def update_online_list(data):
    # 去除大括号，并按逗号分隔
    data = data.strip('{}')
    users = data.split(',')
    online_count.set(f"在线人数: {users[0]}")  # 更新在线人数显示
    online_list.delete(0, tk.END)  # 清空当前列表
    for user in users[1:]:  # 跳过第一个元素（人数），遍历ID
        online_list.insert(tk.END, user)  # 将用户ID添加到列表中

def insert_message(message, align):
    if output_text:
        output_text.configure(state=tk.NORMAL)
        output_text.insert(tk.END, message + '\n', align)
        output_text.configure(state=tk.DISABLED)
        output_text.yview(tk.END)

root = tk.Tk()
root.title("简易聊天室")

prompt_label = tk.Label(root, text="请向聊天室管理员获取信息", font=("", 10), pady=10)
prompt_label.pack()

online_count = tk.StringVar()
online_count.set("在线人数: 未连接")

# 在线列表框架
online_frame = tk.Frame(root, width=200)
online_frame.pack(side=tk.LEFT, fill=tk.Y)

online_label = tk.Label(online_frame, textvariable=online_count)
online_label.pack()

refresh_button = tk.Button(online_frame, text="刷新列表", command=request_online_list)
refresh_button.pack()

online_list = tk.Listbox(online_frame)
online_list.pack(expand=True, fill=tk.BOTH)

# 聊天界面框架
chat_frame = tk.Frame(root)
chat_frame.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)

# 连接控制
connect_frame = tk.Frame(chat_frame)
connect_frame.pack(fill='x')

ip_label = tk.Label(connect_frame, text="IP:")
ip_label.pack(side='left')
ip_entry = tk.Entry(connect_frame)
ip_entry.pack(side='left')
ip_entry.insert(0, SERVER_IP)

port_label = tk.Label(connect_frame, text="端口:")
port_label.pack(side='left')
port_entry = tk.Entry(connect_frame)
port_entry.pack(side='left')
port_entry.insert(0, str(SERVER_PORT))

key_label = tk.Label(connect_frame, text="密钥:")
key_label.pack(side='left')
key_entry = tk.Entry(connect_frame)
key_entry.pack(side='left')
key_entry.insert(0, SECRET_KEY)

connect_button = tk.Button(connect_frame, text="连接", command=connect_server)
connect_button.pack(side='left')

# 聊天输出
output_text = tk.Text(chat_frame, wrap=tk.WORD, state=tk.DISABLED)
output_text.pack(expand=True, fill='both')

# 聊天输入
input_frame = tk.Frame(chat_frame)
input_frame.pack(fill='x')

input_entry = tk.Entry(input_frame)
input_entry.pack(fill='x', side='left', expand=True)

send_button = tk.Button(input_frame, text="发送", command=lambda: send_message(input_entry))
send_button.pack(side='right')

output_text.tag_configure('left', justify='left')
output_text.tag_configure('right', justify='right')

root.mainloop()
