import socket
import threading
import sys
import random
from time_model import Timer  # 确保time_model.Timer已正确实现

# 配置
BUFFER_SIZE = 1024
PACKET_SIZE = 10
WINDOW_SIZE = 4
TIMEOUT = 2


def packetize_bytes(bytes_data):
    """
    将字节数据分块为固定长度的数据包
    每个包10字节，进行序列号的绑定
    """
    packets = []
    seq = 0
    total_size = len(bytes_data)
    for i in range(0, total_size, 8):
        chunk = bytes_data[i : i + 8]  # 每次读取8字节内容
        if len(chunk) < 8:
            chunk = chunk.ljust(8, b"\0")  # 用\0填充至8字节
        flag = 0x0011 if i + 8 >= total_size else 0x0010
        # 构造数据包：Seq (2字节) + Flag (2字节) + Data (8字节)
        packet = seq.to_bytes(2, "big") + flag.to_bytes(2, "big") + chunk
        packets.append(packet)
        seq += 1  # 序列号递增

    return packets


class Sender(threading.Thread):
    def __init__(self, server_socket, client_address, data):
        super().__init__()
        self.server_socket = server_socket  # 共享的服务器套接字
        self.client_address = client_address  # 客户端地址
        self.packets = packetize_bytes(data)
        self.base = 0  # 窗口起点
        self.nextseq = 0  # 下一个要发送的序列号
        self.window_size = WINDOW_SIZE
        self.lock = threading.Lock()  # 多线程锁保护共享变量
        self.timer = Timer(
            TIMEOUT, self.timeout_handler
        )  # 初始化计时器，并设置超时后的回调函数

    def run(self):
        print(f"[DOWNLOAD] 开始发送文件给 {self.client_address}")
        while self.base < len(self.packets):
            with self.lock:
                while (
                    self.nextseq < len(self.packets)
                    and self.nextseq < self.base + self.window_size
                ):
                    # 发送数据包
                    self.server_socket.sendto(
                        self.packets[self.nextseq], self.client_address
                    )
                    print(f"[DOWNLOAD] 发送数据包 Seq={self.nextseq}")
                    if self.base == self.nextseq:
                        self.timer.start()
                    self.nextseq += 1

            try:
                self.server_socket.settimeout(TIMEOUT)
                ack_data, addr = self.server_socket.recvfrom(BUFFER_SIZE)
                if addr != self.client_address:
                    # 忽略来自其他客户端的ACK
                    continue

                ack = int.from_bytes(ack_data[:2], "big")
                print(f"[DOWNLOAD] 收到 ACK: Seq={ack}")

                with self.lock:
                    if ack >= self.base:
                        self.base = ack + 1
                        if self.base == self.nextseq:
                            self.timer.stop()  # 所有包已确认，停止计时器
                        else:
                            self.timer.start()  # 重启计时器

            except socket.timeout:
                print("[DOWNLOAD] 等待 ACK 超时")
                self.timeout_handler()  # 处理超时

        self.timer.stop()
        print(f"[DOWNLOAD] 文件发送完毕给 {self.client_address}")
        # 发送下载完成确认
        self.server_socket.sendto("DOWNLOAD_SUCCESS".encode(), self.client_address)

    def timeout_handler(self):
        """超时处理：重传窗口内所有未确认包"""
        with self.lock:
            print("[DOWNLOAD] 超时，重传窗口内所有未确认包")
            for seq in range(self.base, self.nextseq):
                self.server_socket.sendto(self.packets[seq], self.client_address)
                print(f"[DOWNLOAD] 重传数据包 Seq={seq}")
            self.timer.start()  # 重启计时器
