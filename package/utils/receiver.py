import socket
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9204
BUFFER_SIZE = 1024
PACKET_SIZE = 10
WINDOW_SIZE = 4
TIMEOUT = 2

class Receiver:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((SERVER_HOST, SERVER_PORT))
        self.expected_seq = 0
        self.received_packets = {}  
        self.last_packet_received = False
        
    def receive(self):
        print("接收端启动")
        while True:
            packet, client_address = self.socket.recvfrom(BUFFER_SIZE) #监听后接收
            seq = int.from_bytes(packet[:2], "big") #解析获取序列号
            flag = int.from_bytes(packet[2:4], "big")  # 解析标志位
            data = packet[4:].decode().strip()
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
        """重组接收到的所有数据包为完整消息"""
        message = "".join(
            self.received_packets[seq] for seq in sorted(self.received_packets)
        )
        print(f"重组后的完整消息: {message}")
         
def startReciver():
    receiver = Receiver()
    receiver.receive()

if __name__ == "__main__":
    startReciver()