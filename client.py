import streamlit as st
from sender import Sender
from receiver import Receiver
import socket
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9204

st.title("客户端")

uploaded_file = st.file_uploader("上传文件") 

if uploaded_file is not None:
    if st.button("发送",key="send"):
        bytes_data = uploaded_file.getvalue()
        sender = Sender(9204,bytes_data)
        sender.send()
        sender.close()

if st.button("下载文件"):
    download_request_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # addr, port = download_request_socket.getsockname()
    seq = 0
    flag = 0x0001
    filename = ''
    data = filename.encode().ljust(8, b"\0")
    request_packet = seq.to_bytes(2, "big") + flag.to_bytes(2, "big") + data
    download_request_socket.sendto(request_packet, ("127.0.0.1", 9204))
    download_request_socket.close()
    st.write("下载请求已发送")
    receiver = Receiver(9205)
    receiver.bind()
    receiver.receive()
    st.write("文件下载完成")
