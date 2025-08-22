import win32gui
import dxcam
import cv2
import numpy as np
import os

camera = dxcam.create()

class BaseRecognition(object):

    def __init__(self):
        self.window_title = "三角洲行动  "
        self.temp_save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_save')


    def get_window_rect(self):
        """
        获取游戏窗口的精确位置和尺寸
        """
        hwnd = win32gui.FindWindow(None, self.window_title)
        if hwnd == 0:
            raise Exception("窗口未找到，请确认标题是否正确")

        # 获取窗口边框尺寸
        rect = win32gui.GetWindowRect(hwnd)
        client_rect = win32gui.GetClientRect(hwnd)

        # 计算边框偏移量（适配不同DPI缩放）
        border_width = int((rect[2] - rect[0] - client_rect[2]) // 2)
        title_height = (rect[3] - rect[1] - client_rect[3]) - border_width * 2

        # 实际内容区域坐标
        left = rect[0] + border_width
        top = rect[1] + title_height
        right = left + client_rect[2]
        bottom = top + client_rect[3]

        return (left, top, right, bottom)

    def get_pos_rate(self):
        """获取操作坐标的比例参数"""
        left, top, right, bottom = self.get_window_rect()
        width = right - left
        height = bottom - top
        rate_x = width / 1600
        rate_y = height / 900
        return rate_x, rate_y

    def get_game_full_frame(self):
        """获取完整的游戏窗口（用于测试）"""
        frame = camera.grab(region=self.get_window_rect())
        while frame is None:
            frame = camera.grab(region=self.get_window_rect())
        return frame

    def get_current_frame(self, x, y, width, height):
        """
        在图像上应用掩码，只保留指定区域的图像，其余部分转为全黑。

        参数:
            frame (numpy.ndarray): 输入的图像（如 1920x1080）。
            x (int): 区域的起始 x 坐标。
            y (int): 区域的起始 y 坐标。
            width (int): 区域的宽度。
            height (int): 区域的高度。

        返回:
            numpy.ndarray: 应用掩码后的图像（与输入图像大小相同）。
        """
        rate_x, rate_y = self.get_pos_rate()
        frame = self.get_game_full_frame()
        h, w = frame.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.rectangle(mask, (x, y), (x + int(width * rate_x), y + int(height * rate_y)), 255, -1)  # -1 表示填充矩形
        masked_frame = cv2.bitwise_and(frame, frame, mask=mask)
        return masked_frame

    def get_current_region(self, x, y, width, height):
        """
        截取游戏窗口中的某个区域
        :param x: 区域左上角的x坐标（相对于窗口左上角）
        :param y: 区域左上角的y坐标（相对于窗口左上角）
        :param width: 区域的宽度
        :param height: 区域的高度
        :return: 返回截图的numpy数组
        """
        # 获取窗口位置
        left, top, right, bottom = self.get_window_rect()
        rate_x, rate_y = self.get_pos_rate()
        # 计算实际截图区域
        capture_region = (left + x, top + y, left + x + int(rate_x * width), top + y + int(rate_y * height))
        # 截取指定区域
        frame = camera.grab(region=capture_region)
        while frame is None:
            frame = camera.grab(region=capture_region)
        # 返回截图
        return frame


base_recognition = BaseRecognition()