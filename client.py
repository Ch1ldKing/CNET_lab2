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
        sender = Sender(bytes_data)
        sender.send()
        sender.close()

if st.button("下载文件"):
    download_request_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    request_seq = 0
    request_flag = 0x0001
    request_chunk = "download.txt".ljust(8)
    download_request = (
        request_seq.to_bytes(2, "big")
        + request_flag.to_bytes(2, "big")
        + request_chunk.encode()
    )
    download_request_socket.sendto(download_request, (SERVER_HOST, SERVER_PORT))
    st.write("下载请求已发送")
    download_request_socket.close()
    receiver = Receiver(9205)
    receiver.bind()
    receiver.receive()
    

