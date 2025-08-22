from recognition import recognition
import pyautogui
import time
from safe_mode import start_safe_mode

def move_mouse(x, y):
    """
    将鼠标移动到相对于游戏窗口的指定坐标
    :param x: 相对于窗口左上角的x坐标
    :param y: 相对于窗口左上角的y坐标
    :param window_title: 游戏窗口标题
    """
    # 获取游戏窗口的实际屏幕坐标
    left, top, _, _ = recognition.get_window_rect()

    # 计算目标屏幕坐标
    target_x = left + x
    target_y = top + y

    # 移动鼠标到目标坐标
    pyautogui.moveTo(target_x, target_y)


def get_mouse():
    """
    获取当前鼠标位置，返回相对于游戏窗口的坐标 (x, y)
    :param window_title: 游戏窗口标题
    :return: 相对于窗口左上角的坐标 (x, y)
    """
    # 获取鼠标的屏幕坐标
    screen_x, screen_y = pyautogui.position()

    # 获取游戏窗口的实际屏幕坐标
    left, top, _, _ = recognition.get_window_rect()

    # 计算相对于游戏窗口的坐标
    relative_x = screen_x - left
    relative_y = screen_y - top

    return (relative_x, relative_y)

def max_prebuy():
    # 购买量预备拉满
    move_mouse(1450, 715)
    time.sleep(0.15)
    pyautogui.click()
    time.sleep(0.05)


def buy():
    move_mouse(1371, 776)
    pyautogui.click()
    time.sleep(0.05)

def reset():
    move_mouse(594, 58)
    pyautogui.click()
    time.sleep(0.15)
    price = recognition.get_right_price()
    if price:
        pyautogui.press('esc')
    price = recognition.get_record_price()
    if price:
        move_mouse(168, 112)
        pyautogui.click()
    print("reset")

if __name__ == "__main__":
    start_safe_mode()
    while True:
        # 点击购买子弹
        move_mouse(1329, 218)
        pyautogui.click()
        price = recognition.get_window_rect()
        if price:
            buy()
            pyautogui.press('esc')
        else:
            reset()
            continue
        # 交易记录
        move_mouse(379, 112)
        pyautogui.click()
        price = recognition.get_record_price()
        print(price)
        move_mouse(168, 112)
        pyautogui.click()
        if price:
            if price<590:
                move_mouse(1329, 218)
                pyautogui.click()
                temp = recognition.get_window_rect()
                if temp:
                    max_prebuy()
                    for i in range(5):
                        buy()
                else:
                    reset()
                    continue
                pyautogui.press('esc')
        else:
            reset()
            continue
        time.sleep(7)