import streamlit as st
from sender import Sender
from receiver import Receiver
import threading
import sys
sys.path.append("../package/")

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9204
BUFFER_SIZE = 12  # 每个数据包：2字节序列号 + 2字节标志位 + 8字节数据
WINDOW_SIZE = 4
TIMEOUT = 2

