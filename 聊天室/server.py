# 编译exe程序
# Cmd : pyinstaller --onefile
# server.py build

import socket
import select

HOST = '0.0.0.0'
PORT = 8080
SECRET_KEY = 'your_secret_key'

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen()
server_socket.setblocking(0)

authenticated_clients = []  # 存储已验证的客户端套接字
clients = {}  # 存储所有客户端套接字和它们的数据

print(f"服务端启动，监听 {HOST}:{PORT}...")

sockets_list = [server_socket]

def receive_message(client_socket):
    try:
        message_header = client_socket.recv(10)
        if not len(message_header):
            return False
        message_length = int(message_header.decode('utf-8').strip())
        return {"header": message_header, "data": client_socket.recv(message_length)}
    except:
        return False

def send_message(client_socket, message):
    """发送消息给客户端，包括消息头部和消息数据。"""
    message_header = f"{len(message):<10}".encode('utf-8')
    client_socket.send(message_header + message)

def broadcast_message(message, exclude_socket=None):
    """广播消息给所有已验证的客户端，除了指定的客户端。"""
    for client in authenticated_clients:
        if client != exclude_socket:
            send_message(client, message)

def broadcast_current_count():
    """广播当前在线人数给所有已验证的客户端。"""
    count_message = f"当前人数 {len(authenticated_clients)}".encode('utf-8')
    for client in authenticated_clients:
        send_message(client, count_message)
        
def handle_list_command(notified_socket):
    """处理/list命令，发送当前在线用户列表。"""
    # 构建用户ID列表
    user_ids = [clients[client_socket]['data'].decode('utf-8') for client_socket in authenticated_clients]
    # 构建格式化的消息字符串
    list_message = f'{{{len(authenticated_clients)},{",".join(user_ids)}}}'
    encoded_list_message = list_message.encode('utf-8')
    # 发送给请求的客户端
    send_message(notified_socket, encoded_list_message)

while True:
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    for notified_socket in read_sockets:
        if notified_socket == server_socket:
            client_socket, client_address = server_socket.accept()
            print(f"{client_address} 请求加入房间，正在验证密钥...")
            sockets_list.append(client_socket)
            pass
        else:
            message = receive_message(notified_socket)

            if message is False:
                client_ip_port = notified_socket.getpeername()  # 获取断开连接的客户端地址
                print(f"{client_ip_port} 断开了连接")
                sockets_list.remove(notified_socket)
                if notified_socket in authenticated_clients:
                    authenticated_clients.remove(notified_socket)
                    if notified_socket in clients:  # 确保客户端在clients字典中
                        leave_message = f"{clients[notified_socket]['data'].decode('utf-8')} 离开了房间".encode('utf-8')
                        broadcast_message(leave_message, exclude_socket=notified_socket)
                    broadcast_current_count()
                if notified_socket in clients:
                    del clients[notified_socket]
                continue

            if notified_socket not in authenticated_clients:
                key = message['data'].decode('utf-8')
                if key == SECRET_KEY:
                    authenticated_clients.append(notified_socket)
                    print(f"{client_address} 密钥验证成功")
                    client_ip_simplified = client_address[0].replace('.', '')[:6]
                    clients[notified_socket] = {"header": message['header'], "data": client_ip_simplified.encode('utf-8')}
                    welcome_message = f"欢迎加入聊天室！".encode('utf-8')
                    send_message(notified_socket, welcome_message)
                    join_message = f"{client_ip_simplified} 加入了房间".encode('utf-8')
                    broadcast_message(join_message, exclude_socket=notified_socket)
                    broadcast_current_count()
                else:
                    print(f"{notified_socket.getpeername()} 密钥验证失败")
                    sockets_list.remove(notified_socket)
                    notified_socket.close()
            else:
                if message['data'].decode('utf-8') == '/list':
                    print(f"{notified_socket.getpeername()} 执行了/list")
                    handle_list_command(notified_socket)
                else:
                    # 处理已验证客户端的其他消息转发逻辑
                    print(f"{notified_socket.getpeername()} 发送: {message['data'].decode('utf-8')}")
                    user_id = clients[notified_socket]['data'].decode('utf-8')
                    message_content = message['data'].decode('utf-8')
                    combined_message = f"{user_id} : {message_content}".encode('utf-8')  # 合并ID和消息内容

                    for client_socket in authenticated_clients:
                        if client_socket != notified_socket:
                            send_message(client_socket, combined_message)  # 使用send_message函数发送合并后的消息

    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        if notified_socket in authenticated_clients:
            authenticated_clients.remove(notified_socket)
            if notified_socket in clients:
                leave_message = f"{clients[notified_socket]['data'].decode('utf-8')} 离开了房间".encode('utf-8')
                broadcast_message(leave_message, exclude_socket=notified_socket)
                broadcast_current_count()
            if notified_socket in clients:
                del clients[notified_socket]
