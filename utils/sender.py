import socket
from lab2.utils.timer import Timer
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9204
BUFFER_SIZE =  1024
PACKET_SIZE = 10
WINDOW_SIZE = 4
TIMEOUT = 2

def send():
    sendsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    message = "这是一条测试消息。你好啊，receiver！This is a test message. Hello, receiver!"
    packets = packetize_message(message)
    base = 0
    nextseq = 0
    timer 

    while base < len(packets):

        while nextseq < len(packets) and nextseq < base + WINDOW_SIZE:
            sendsocket.sendto(packets[nextseq], (SERVER_HOST, SERVER_PORT))
            print("发送数据包", nextseq)
            nextseq += 1
            if nextseq == base:

                
        
        ack_data , _ = sendsocket.recvfrom(BUFFER_SIZE)
        ack = int.from_bytes(ack_data[:2], "big")
        print("收到ACK", ack)
        base = ack + 1

        

        
        




 



def packetize_message(message):
    """将消息拆分为固定长度的数据包，每个包10字节"""
    packets = []
    seq = 0

    # 每次取出8字节内容
    for i in range(0, len(message), 8):
        chunk = message[i : i + 8]  # 获取当前分片
        if len(chunk) < 8:
            chunk = chunk.ljust(8)  # 用空格填充至8字节

        # 构造数据包：Seq (2字节) + Data (8字节)
        packet = seq.to_bytes(2, "big") + chunk.encode()
        packets.append(packet)
        seq += 1  # 序列号递增

    return packets


def reassemble_message(received_packets):
    """将收到的多个数据包按序重组为完整消息"""
    # 按序列号排序数据包
    received_packets.sort(key=lambda x: int.from_bytes(x[:2], "big"))

    # 拼接所有数据部分，并去除填充的空格
    message = "".join([packet[2:].decode().strip() for packet in received_packets])
    return message
