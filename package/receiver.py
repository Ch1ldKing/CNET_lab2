import socket
import threading
import sys
import signal

sys.path.append("../package/")

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9205
BUFFER_SIZE = 12  # 每个数据包：2字节序列号 + 2字节标志位 + 8字节数据
WINDOW_SIZE = 4
TIMEOUT = 2

class Receiver:
    def __init__(self,port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.expected_seq = 0  # 期望的下一个序列号
        self.port = port
        self.received_packets = {}  # 存储接收到的数据包
        self.lock = threading.Lock()  # 用于线程安全
        self.message_bytes = b""  # 存储完整字节数据
        self.message_received_event = threading.Event()  # 用于通知消息接收完成
        self.packet_received_callback = None  # 回调函数，用于通知外部程序接收的包序列号
        self.last_packet_received = False

    def bind(self):
        self.socket.bind((SERVER_HOST, self.port))

    def close(self):   
        self.socket.close()

    def receive(self):
        print("接收端启动")
        while True:
            packet, client_address = self.socket.recvfrom(BUFFER_SIZE)  # 监听后接收
            seq = int.from_bytes(packet[:2], "big")  # 解析获取序列号
            flag = int.from_bytes(packet[2:4], "big")  # 解析标志位
            data = packet[4:]
            print(f"收到数据包: Seq = {seq}, Data = {data}")

            if seq == self.expected_seq:
                self.received_packets[seq] = data
                self.expected_seq += 1
            else:
                print(f"收到重复数据包: Seq = {seq}")

            if flag == 0x0001:  # 检测是否为最后一个包
                self.last_packet_received = True

            ack = self.expected_seq - 1
            if ack >= 0:
                ack_packet = ack.to_bytes(2, "big")
                self.socket.sendto(ack_packet, client_address)
                print(f"发送ACK: {ack}")
                if self.last_packet_received:
                    break

        print("所有包已接收完毕")
        self.reassemble_message()
        self.socket.close()


    def reassemble_message(self):
        """重组所有数据包为完整字节数据并保存为txt文件"""
        self.message_bytes = b"".join(
            self.received_packets[seq] for seq in sorted(self.received_packets)
        )
        print(f"重组后的完整字节数据: {self.message_bytes}")

        # 将字节数据解码为字符串并写入txt文件
        with open("received_message.txt", "w", encoding="utf-8") as f:
            message = self.message_bytes.decode("utf-8").rstrip('\x00')
            print(f"消息内容: {message}")
            message = message.replace("\r\n", "\n")
            f.write(message)
        print("消息已保存为 received_message.txt")

        # 重置状态以接收下一条消息
        self.received_packets.clear()
        self.expected_seq = 0

    def get_message_bytes(self):
        """等待消息接收完成并返回完整的字节数据"""
        self.message_received_event.wait()  # 等待消息接收完成
        self.message_received_event.clear()  # 重置事件以接收下一条消息
        return self.message_bytes

    def __del__(self):
        self.close()

def start_receiver():
    receiver = Receiver(9204)
    receiver.bind()
    receiver.receive()

if __name__ == "__main__":
    start_receiver()
