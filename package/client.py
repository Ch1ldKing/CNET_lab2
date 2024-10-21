import streamlit as st
from sender import Sender
st.title("客户端")

uploaded_file = st.file_uploader("上传文件") 

if uploaded_file is not None:
    if st.button("发送",key="send"):
        bytes_data = uploaded_file.getvalue()
        sender = Sender(bytes_data)
        sender.send()
        sender.close()
