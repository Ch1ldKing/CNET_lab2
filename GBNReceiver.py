import socket
import threading
import os

# 配置
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9204
BUFFER_SIZE = 12  # 每个数据包：2字节序列号 + 2字节标志位 + 8字节数据

# 文件存储目录
UPLOAD_DIR = "uploads"

# 确保目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)


class GBNReceiver(threading.Thread):
    def __init__(self, server_socket, client_address, initial_packet=None):
        super().__init__()
        self.server_socket = server_socket  # 传入的服务器套接字地址，用的是服务器（客户端）的套接字
        self.client_address = client_address  # 客户端地址（只在作服务器时有效）
        self.initial_packet = initial_packet  # 初始数据包
        self.expected_seq = 0  # 期望的下一个序列号
        self.received_packets = {}  # 存储接收到的数据包
        self.lock = threading.Lock()  # 用于线程安全
        self.message_bytes = b""  # 存储完整字节数据
        self.last_packet_received = False  # 是否接收到最后一个包

    def run(self):
        print(f"[UPLOAD] 开始接收来自 {self.client_address} 的文件")
        filepath = os.path.join(
            UPLOAD_DIR,
            f"received_from_{self.client_address[0]}_{self.client_address[1]}.txt",
        )
        with open(filepath, "wb") as f:

            if self.initial_packet is not None:
                # 处理初始数据包
                seq = int.from_bytes(self.initial_packet[:2], "big")
                flag = int.from_bytes(self.initial_packet[2:4], "big")
                data = self.initial_packet[4:]

                print(
                    f"[UPLOAD] 收到初始数据包: Seq={seq}, Flag=0x{flag:04X}, Data={data}"
                )

                if seq == self.expected_seq:
                    f.write(data)
                    self.received_packets[seq] = data
                    self.expected_seq += 1
                    print(f"[UPLOAD] 写入初始数据包 Seq={seq}")
                    
                    #TODO 如果第一个包就是最后一个包怎么办。正常不考虑这种情况
                    if flag == 0x0011:
                        # 最后一个上传包
                        self.last_packet_received = True
                        print("[UPLOAD] 收到最后一个数据包")

                # 发送ACK
                if self.expected_seq > 0:
                    ack = (self.expected_seq - 1).to_bytes(2, "big")
                    self.server_socket.sendto(ack, self.client_address)
                    print(f"[UPLOAD] 发送ACK: Seq={self.expected_seq - 1}")

            while not self.last_packet_received:
                try:
                    packet, addr = self.server_socket.recvfrom(BUFFER_SIZE)
                    
                    if addr != self.client_address:
                        # 忽略来自其他客户端的数据包
                        continue

                    seq = int.from_bytes(packet[:2], "big")
                    flag = int.from_bytes(packet[2:4], "big")
                    data = packet[4:]

                    print(
                        f"[UPLOAD] 收到数据包: Seq={seq}, Flag=0x{flag:04X}, Data={data}"
                    )

                    with self.lock:
                        if seq == self.expected_seq:
                            f.write(data)
                            self.received_packets[seq] = data
                            self.expected_seq += 1
                            print(f"[UPLOAD] 写入数据包 Seq={seq}")

                            if flag == 0x0011:
                                # 最后一个上传包
                                self.last_packet_received = True
                                print("[UPLOAD] 收到最后一个数据包")
                        else:
                            print(f"[UPLOAD] 收到重复或乱序数据包: Seq={seq}")

                        # 发送ACK
                        if self.expected_seq > 0: #如果第一个包都没收到，就不发ack了
                            ack = (self.expected_seq - 1).to_bytes(2, "big")
                            self.server_socket.sendto(ack, self.client_address)
                            print(f"[UPLOAD] 发送ACK: Seq={self.expected_seq - 1}")

                except Exception as e:
                    print(f"[UPLOAD] 处理上传时发生错误: {e}")
                    break

        print(f"[UPLOAD] 文件接收完毕，保存在 '{filepath}'")
        # 可以在这里添加进一步处理，如通知用户上传成功等
