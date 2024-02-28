# 编译exe程序
# Cmd : pyinstaller --onefile
# client.pyw build

import tkinter as tk
from threading import Thread
import socket
import time

SERVER_IP = "47.96.78.148"
SERVER_PORT = 8080
SECRET_KEY = "your_secret_key"

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
                client_socket.setblocking(True)  # Changed to blocking mode for the receiving thread

                # 发送密钥以验证
                key = secret_key.encode('utf-8')
                key_header = f"{len(key):<10}".encode('utf-8')
                client_socket.send(key_header + key)

                connected = True
                root.title("简易聊天室 - 已连接")
                connect_button.config(text="断开")
                ip_entry.config(state='readonly')
                port_entry.config(state='readonly')
                key_entry.config(state='readonly')

                # Start receiving thread
                Thread(target=receive_messages_loop, daemon=True).start()
            except Exception as e:
                print("连接失败:", e)
    else:
        disconnect_server()

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

def send_message(input_entry):
    global client_socket
    if client_socket and connected:
        message = input_entry.get().strip()
        if message:
            input_entry.delete(0, tk.END)  # 清空输入框
            message = message.encode('utf-8')
            message_header = f"{len(message):<10}".encode('utf-8')
            client_socket.send(message_header + message)

def receive_messages_loop():
    global client_socket, connected
    while connected:
        try:
            message_header = client_socket.recv(10)
            if not len(message_header):
                print("Connection closed by the server.")
                break
            message_length = int(message_header.decode('utf-8').strip())
            message = client_socket.recv(message_length).decode('utf-8')

            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            message = f"[{current_time}] {message}"
            insert_message(message, 'left')
        except Exception as e:
            print("Error receiving message:", e)
            break
    disconnect_server()

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

connect_frame = tk.Frame(root)
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

output_text = tk.Text(root, wrap=tk.WORD, state=tk.DISABLED)
output_text.pack(expand=True, fill='both')

input_entry = tk.Entry(root)
input_entry.pack(fill='x', side='left', expand=True)

send_button = tk.Button(root, text="发送", command=lambda: send_message(input_entry))
send_button.pack(side='right')

output_text.tag_configure('left', justify='left')
output_text.tag_configure('right', justify='right')

root.mainloop()
