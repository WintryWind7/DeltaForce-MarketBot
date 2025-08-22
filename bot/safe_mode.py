import threading
import time
import sys
from pynput import mouse
import os
from log import log

# 全局变量
is_human_activity = False
last_position = None
last_time = None

# 鼠标移动事件回调函数
def on_move(x, y):
    global is_human_activity, last_position, last_time

    current_time = time.time()
    if last_position and last_time:
        # 计算移动距离和时间差
        dx = x - last_position[0]
        dy = y - last_position[1]
        distance = (dx**2 + dy**2) ** 0.5  # 欧几里得距离
        time_diff = current_time - last_time

        # 计算移动速度
        speed = distance / time_diff if time_diff > 0 else 0

        # 如果速度较慢且距离较大，则认为是人类操作
        if speed < 2000000 and distance > 3:  # 调整阈值以适应你的需求
            is_human_activity = True

    # 更新上一次的位置和时间
    last_position = (x, y)
    last_time = current_time

# 安全线程
def safety_monitor():
    global is_human_activity
    while True:
        if is_human_activity:
            log.write('检测到用户操作，程序即将停止...', level='warning')
            log.shutdown()
            os._exit(0)  # 强制终止程序
        time.sleep(0.1)  # 每 0.1 秒检查一次

# 启动鼠标监听器
def start_mouse_listener():
    with mouse.Listener(on_move=on_move) as listener:
        listener.join()

def start_safe_mode():
    # 启动安全线程
    safety_thread = threading.Thread(target=safety_monitor, daemon=True)
    safety_thread.start()

    # 启动鼠标监听器线程
    mouse_listener_thread = threading.Thread(target=start_mouse_listener, daemon=True)
    mouse_listener_thread.start()

    log.write('启动安全线程!', level='info')

if __name__ == "__main__":

    start_safe_mode()