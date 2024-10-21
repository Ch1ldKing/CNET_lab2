import threading
import time


class Timer:
    """独立的计时器类，用于管理超时重传"""

    def __init__(self, timeout, timeout_handler):
        """
        初始化计时器
        :param timeout: 超时时间（秒）
        :param timeout_handler: 超时触发的重传回调函数
        """
        self.timeout = timeout
        self.timeout_handler = timeout_handler  # 回调函数
        self.timer_event = threading.Event()  # 控制计时器的事件对象
        self.timer_thread = None  # 计时器线程对象

    def start(self):
        """启动计时器线程"""
        if self.timer_thread and self.timer_thread.is_alive():
            self.stop()  # 停止正在运行的计时器
        self.timer_event.clear()  # 清除事件状态 
        self.timer_thread = threading.Thread(target=self.run)
        self.timer_thread.start()

    def run(self):
        """计时器逻辑，在超时后调用回调函数"""
        if not self.timer_event.wait(self.timeout):  # 等待超时或停止事件触发
            print("计时器超时")
            self.timeout_handler()  # 执行重传回调函数

    def stop(self):
        """停止计时器"""
        self.timer_event.set()  # 设置事件状态，通知线程退出
