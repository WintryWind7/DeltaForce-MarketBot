"""
TCP Socket 最简单的例子
演示客户端和服务器如何通信
"""

import socket
import threading
import time

# ============================================================
# 服务器端（Server）- 相当于"接电话的人"
# ============================================================
def server():
    print("【服务器】启动中...")
    
    # 1. 创建Socket（买一部电话）
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #                              ↑ IPv4      ↑ TCP协议
    
    # 2. 绑定地址和端口（安装电话号码）
    server_socket.bind(('localhost', 8888))
    #                    ↑ IP地址    ↑ 端口号
    
    # 3. 开始监听（等待来电）
    server_socket.listen(1)  # 最多1个等待连接
    print("【服务器】等待客户端连接... (端口8888)")
    
    # 4. 接受连接（接听电话）
    client_socket, client_address = server_socket.accept()
    print(f"【服务器】客户端已连接: {client_address}")
    
    # 5. 接收数据（听对方说话）
    data = client_socket.recv(1024)  # 最多接收1024字节
    message = data.decode('utf-8')
    print(f"【服务器】收到消息: {message}")
    
    # 6. 发送响应（回复对方）
    response = "你好，我收到了你的消息！"
    client_socket.send(response.encode('utf-8'))
    print(f"【服务器】发送响应: {response}")
    
    # 7. 关闭连接（挂断电话）
    client_socket.close()
    server_socket.close()
    print("【服务器】连接已关闭")

# ============================================================
# 客户端（Client）- 相当于"打电话的人"
# ============================================================
def client():
    time.sleep(0.5)  # 等待服务器启动
    
    print("\n【客户端】启动中...")
    
    # 1. 创建Socket（买一部电话）
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # 2. 连接服务器（拨打电话）
    print("【客户端】正在连接服务器...")
    client_socket.connect(('localhost', 8888))
    print("【客户端】已连接到服务器")
    
    # 3. 发送数据（说话）
    message = "你好，服务器！"
    client_socket.send(message.encode('utf-8'))
    print(f"【客户端】发送消息: {message}")
    
    # 4. 接收响应（听回复）
    data = client_socket.recv(1024)
    response = data.decode('utf-8')
    print(f"【客户端】收到响应: {response}")
    
    # 5. 关闭连接（挂断电话）
    client_socket.close()
    print("【客户端】连接已关闭")

# ============================================================
# 运行演示
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("TCP Socket 通信演示")
    print("=" * 60)
    
    # 在两个线程中运行服务器和客户端
    server_thread = threading.Thread(target=server)
    client_thread = threading.Thread(target=client)
    
    server_thread.start()
    client_thread.start()
    
    server_thread.join()
    client_thread.join()
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)
