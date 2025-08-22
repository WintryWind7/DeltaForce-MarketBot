import os.path
import time
import cv2
import easyocr
from .ClassBaseRecognition import BaseRecognition

digit_reader = easyocr.Reader(['en'], gpu=False, recog_network='english_g2', model_storage_directory='model_cache')

class Recognition(BaseRecognition):

    def __init__(self):
        super().__init__()

    def ocr_recogn(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 88, 255, cv2.THRESH_BINARY_INV)
        # easyocr
        results = digit_reader.readtext(binary, allowlist='0123456789', decoder='beamsearch',  )
        text = ''.join([res[1] for res in results])
        # cv2.imwrite(f'./data/{text}.jpg', binary)
        return text


    def get_record_price(self, save_image=False, save_path=None):
        """
        获取交易记录的最新价格
        """

        for i in range(3):
            frame = self.get_current_region(370, 258, 100, 20)
            try:
                text = self.ocr_recogn(frame)
                # text应当是识别出来的结果，判断是否全为数字，
                if text.isdigit():
                    if save_image:
                        cv2.imwrite(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{str(text)}.jpg"), frame)
                    # if len(text) >= len(str(low_price)):
                    return int(text)
            except:
                pass
            time.sleep(0.3)
        # 判断识别出来的价格是否合法（已判断）
        # 返回False，代表异常，外部需要跳出
        # log("未识别到价格", level='warning')
        if frame is not None:
            if save_image:
                if save_path:
                    cv2.imwrite(os.path.join(save_path, 'None.jpg'), frame)
                else:
                    cv2.imwrite(os.path.join(self.temp_save_path, 'None.jpg'), frame)

        return False

    def get_buy_price(self, save_image=False):
        """
        获取价格
        low_price:最低价格:不会低于这个价格
        """
        # 多次循环，直到检测出合法价格
        time.sleep(0.05)
        # lth = len(str(low_price))
        # print(low_price, lth)
        # frame = capture_window_region(1401 - 5 * lth, 739, 9 * lth + ((lth - 1) // 3), 20)
        for i in range(5):
            frame = self.get_current_region(1350, 739, 90, 20)
            try:
                text = self.ocr_recogn(frame)
                # text应当是识别出来的结果，判断是否全为数字，
                if text.isdigit():
                    # if len(text) >= len(str(low_price)):
                    return int(text)
            except:
                pass
            time.sleep(0.3)
        # 判断识别出来的价格是否合法（已判断）
        # 返回False，代表异常，外部需要跳出
        # log("未识别到价格", level='warning')
        if save_image:
            cv2.imwrite("none.jpg", frame)
        return False


    def get_sell_price(self, save_image=False):

        for i in range(5):
            frame = self.get_current_region(1060, 537, 65, 20)
            try:
                text = self.ocr_recogn(frame)
                # text应当是识别出来的结果，判断是否全为数字，
                if text.isdigit():
                    # if len(text) >= len(str(low_price)):
                    if save_image:
                        cv2.imwrite("123.jpg", frame)
                    return int(text)
            except:
                pass
            time.sleep(0.3)
        # 判断识别出来的价格是否合法（已判断）
        # 返回False，代表异常，外部需要跳出
        # log("未识别到价格", level='warning')

        cv2.imwrite("none_sell.jpg", frame)
        return False


recognition = Recognition()
if __name__ == '__main__':

    print(recognition.get_record_price(save_image=True))
    print(recognition.temp_save_path)

