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
        packet = seq.to_bytes(2, "big") + flag.to_bytes(2,"big") + chunk.encode()   
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
