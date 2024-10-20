import socket
from time_model import Timer
from threading import Lock
import random

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9204
BUFFER_SIZE =  1024
PACKET_SIZE = 10
WINDOW_SIZE = 4
TIMEOUT = 2

class Sender:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.message = "这是一条测试消息。你好啊，receiver！This is a test message. Hello, receiver!"
        self.packets = packetize_message(self.message)
        self.base = 0  # 窗口起点
        self.nextseq = 0  # 下一个要发送的序列号
        self.window_size = WINDOW_SIZE
        self.lock = Lock()  # 多线程锁保护共享变量
        self.timer = Timer(TIMEOUT, self.timeout_handler) # 初始化计时器，并设置超时后的回调函数

    def send(self):
        print("发送端启动")
        while self.base < len(self.packets):
            while (
                self.nextseq < len(self.packets) and self.nextseq < self.base + WINDOW_SIZE
            ):
                if random.random() < 0.5:  # 假设丢包概率为 20%
                    self.socket.sendto(self.packets[self.nextseq], (SERVER_HOST, SERVER_PORT))
                    print("发送数据包", self.nextseq)
                else:
                    print("丢弃数据包", self.nextseq)
                self.nextseq += 1
                if self.nextseq == self.base:
                    self.timer.start()

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
                self.socket.sendto(packet, (SERVER_HOST, SERVER_PORT))
                print(f"重传数据包: Seq = {seq}")

            self.timer.start()  # 重启计时器

    def close(self):
        """关闭socket连接"""
        self.socket.close()


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
        flag = 0x0001 if seq == total_packets - 1 else 0x0000
        # 构造数据包：Seq (2字节) + Data (8字节)
        packet = seq.to_bytes(2, "big") + flag.to_bytes(2, "big") + chunk.encode()
        packets.append(packet)
        seq += 1  # 序列号递增

    return packets

def startSender():
    sender = Sender()
    sender.send()
    sender.close()

if __name__ == "__main__":
    startSender() 