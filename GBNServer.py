import socket
import threading
import sys

# 引入修改后的 Receiver 和 Sender 类
# 确保 Receiver 和 Sender 类在同一目录下，或者正确设置导入路径
from GBNReceiver import GBNReceiver  # 假设将 Receiver 类保存为 receiver.py
from sender import Sender  # 假设将 Sender 类保存为 sender.py

# 配置
SERVER_HOST = "127.0.0.1"  # 监听所有可用的接口
SERVER_PORT = 9204
BUFFER_SIZE = 12  # 每个数据包：2字节序列号 + 2字节标志位 + 8字节数据
SEPARATOR = " "  # 用于分割请求中的不同部分


def handle_request(server_socket, initial_packet, client_address):
    """
    根据初始数据包的 Flag 位，决定是上传还是下载请求
    """
    seq = int.from_bytes(initial_packet[:2], "big")
    flag = int.from_bytes(initial_packet[2:4], "big")
    data = initial_packet[4:]

    print(
        f"[REQUEST] 来自 {client_address} 的请求: Seq={seq}, Flag=0x{flag:04X}, Data={data}"
    )

    if flag == 0x0010:
        # 上传请求
        print(f"[REQUEST] {client_address} 请求上传文件")
        receiver = GBNReceiver(server_socket, client_address, initial_packet)
        receiver.run()
    elif flag == 0x0001:
        # 下载请求
        file_path = ('downloads/downloads.txt')
        with open(file_path, "rb") as f:
            byte_data = f.read()
        sender = Sender(9205, byte_data)
        sender.send()
        sender.close()
    else:
        # 未知的请求类型
        error_message = "ERROR: 未知的请求类型".encode()
        server_socket.sendto(error_message, client_address)
        print(f"[REQUEST] 未知的 Flag 位 0x{flag:04X} 来自 {client_address}")

def start_server():
    # 创建UDP套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    print(f"[*] UDP 服务器正在监听 {SERVER_HOST}:{SERVER_PORT}")

    while True:
        try:
            # 接收初始请求
            print("[MAIN] 等待请求...")
            packet, client_address = server_socket.recvfrom(BUFFER_SIZE)
            print(f"[MAIN] 接收到来自 {client_address} 的初始数据包")
            # 创建一个新的线程来处理该请求
            # request_thread = threading.Thread(
            #     target=handle_request, args=(server_socket, packet, client_address)
            # )
            # request_thread.start()
            handle_request(server_socket, packet, client_address)
            print(f"[MAIN] 接收来自 {client_address} 的请求处理完成")
        except KeyboardInterrupt:
            print("\n[!] 服务器关闭")
            server_socket.close()
            sys.exit(0)
        except Exception as e:
            print(f"[ERROR] 发生错误: {e}")


if __name__ == "__main__":
    # 确保上传和下载目录存在
    import os

    os.makedirs("uploads", exist_ok=True)
    os.makedirs("downloads", exist_ok=True)
    start_server()
