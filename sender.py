import socket
from  time_model import Timer
from threading import Lock
import random
import sys
sys.path.append("../package/")

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9204
BUFFER_SIZE =  1024
PACKET_SIZE = 10
WINDOW_SIZE = 4
TIMEOUT = 2

class Sender:
    def __init__(self, port, data):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.packets = packetize_bytes(data)
        self.port = port    
        self.base = 0  # 窗口起点
        self.nextseq = 0  # 下一个要发送的序列号
        self.window_size = WINDOW_SIZE
        self.lock = Lock()  # 多线程锁保护共享变量
        self.timer = Timer(TIMEOUT, self.timeout_handler) # 初始化计时器，并设置超时后的回调函数

    def send(self):

        print("发送端启动")
        print(self.packets)
        while self.base < len(self.packets):
            while (
                self.nextseq < len(self.packets) and self.nextseq < self.base + WINDOW_SIZE
            ):
                # if random.random() < 0.8:  # 假设丢包概率为 50%
                self.socket.sendto(self.packets[self.nextseq], (SERVER_HOST, self.port))
                print("发送数据包", self.nextseq)
                # else:
                #     print("丢弃数据包", self.nextseq)
                if self.nextseq == self.base:
                    self.timer.start()
                self.nextseq += 1

            try:
                ack_data, _ = self.socket.recvfrom(BUFFER_SIZE)
                ack = int.from_bytes(ack_data[:2], "big")
                print(f"收到 ACK: Seq = {ack}")

                with self.lock:
                    if ack >= self.base:
                        self.base = ack + 1
                        if self.base == self.nextseq:
                            self.timer.stop()  # 所有包已确认，停止计时器
                        else:
                            self.timer.start()  # 重启计时器

            except socket.timeout:
                print("等待 ACK 超时")
                self.timeout_handler()  # 处理超时

    def timeout_handler(self):
        """超时处理：重传窗口内所有未确认包"""
        with self.lock:

            for seq in range(self.base, self.nextseq):
                packet = self.packets[seq]
                self.socket.sendto(packet, (SERVER_HOST, self.port))
                print(f"重传数据包: Seq = {seq}")

            self.timer.start()  # 重启计时器

    def close(self):
        """关闭socket连接"""
        self.socket.close()



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


def packetize_message(message):
    """将消息拆分为固定长度的数据包，每个包10字节"""
    packets = []
    seq = 0
    total_packets = (len(message) + 7) // 8  # 计算总包数
    # 每次取出8字节内容
    for i in range(0, len(message), 8):
        chunk = message[i : i + 8]  # 获取当前分片
        if len(chunk) < 8:
            chunk = chunk.ljust(8)  # 用空格填充至8字节
        flag = 0x0011 if seq == total_packets - 1 else 0x0010
        # 构造数据包：Seq (2字节) + Data (8字节)
        packet = seq.to_bytes(2, "big") + flag.to_bytes(2, "big") + chunk.encode()
        packets.append(packet)
        seq += 1  # 序列号递增

    return packets

def startSender():
    file_path = "./test.txt"  # 替换为你的文件路径

    with open(file_path, "rb") as file:
        byte_data = file.read()

    sender = Sender(byte_data)
    sender.send()
    sender.close()

if __name__ == "__main__":
    startSender() 
