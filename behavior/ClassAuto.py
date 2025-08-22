import pyautogui

from recognition.ClassBaseRecognition import base_recognition
import time

class Auto(object):

    def __init__(self):
        pass


    def move_mouse(self, x, y):
        """
        将鼠标移动到相对于游戏窗口的指定坐标
        :param x: 相对于窗口左上角的x坐标
        :param y: 相对于窗口左上角的y坐标
        :param window_title: 游戏窗口标题
        """
        # 获取游戏窗口的实际屏幕坐标
        left, top, _, _ = base_recognition.get_window_rect()
        rate_x, rate_y = base_recognition.get_pos_rate()
        # 计算目标屏幕坐标
        target_x = left + x
        target_y = top + y

        # 移动鼠标到目标坐标
        pyautogui.moveTo(int(target_x*rate_x), int(target_y*rate_y))

    def max_prebuy(self):
        """
        将预备购买量拉满
        """
        self.move_mouse(1450, 715)
        time.sleep(0.15)
        pyautogui.click()
        time.sleep(0.05)

    def buy(self):
        self.move_mouse(1371, 776)
        pyautogui.click()
        time.sleep(0.05)


    def press_left(self):
        """鼠标左键"""
        pyautogui.click()


    def press_esc(self):
        """esc键"""
        pyautogui.press('esc')
