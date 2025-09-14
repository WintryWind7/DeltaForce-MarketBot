from DeltaForceRecognize import DeltaForceRecognize
import pyautogui
import time
import numpy as np
from PIL import Image

class DeltaForceClass(DeltaForceRecognize):
    def __init__(self):
        super().__init__()
        # 导入pyautogui并借用其DPI感知
        import pyautogui
        # 自动查找DeltaForce进程
        self.find_deltaforce_process()
    
    def get_balance(self, m3_ratio=(0.8066, 0.0866), m4_ratio=(0.7555, 0.2777), m5_ratio=(0.8566, 0.2914)):
        """
        识别账户余额
        
        Args:
            m3_ratio: 点击位置的比例坐标 (x, y)
            m4_ratio: 截图区域左上角的比例坐标 (x, y)
            m5_ratio: 截图区域右下角的比例坐标 (x, y)
            
        Returns:
            int: 识别出的余额数值，识别失败返回None
        """
        try:
            # 1. 点击m3位置
            m3_screen = self.ratio_to_screen_coords(m3_ratio[0], m3_ratio[1])
            pyautogui.click(m3_screen[0], m3_screen[1])
            time.sleep(0.5)  # 等待界面响应
            
            # 2. 获取截图区域坐标
            m4_screen = self.ratio_to_screen_coords(m4_ratio[0], m4_ratio[1])
            m5_screen = self.ratio_to_screen_coords(m5_ratio[0], m5_ratio[1])
            
            # 3. 计算截图区域
            left = min(m4_screen[0], m5_screen[0])
            top = min(m4_screen[1], m5_screen[1])
            right = max(m4_screen[0], m5_screen[0])
            bottom = max(m4_screen[1], m5_screen[1])
            
            # 4. 截图指定区域
            screenshot = pyautogui.screenshot(region=(left, top, right-left, bottom-top))
            screenshot_array = np.array(screenshot)
            
            # 5. 使用OCR识别，应用allowlist只识别数字
            results = self.ocr.reader.readtext(
                screenshot_array,
                allowlist='1234567890',
                width_ths=0.7,
                height_ths=0.7,
                text_threshold=0.5,
                decoder='beamsearch'
            )
            
            # 6. 处理识别结果
            if results:
                # 合并所有识别到的数字
                combined_text = ""
                for (bbox, text, confidence) in results:
                    # 只保留数字字符
                    filtered_text = ''.join(char for char in text if char.isdigit())
                    combined_text += filtered_text
                
                if combined_text:
                    balance = int(combined_text)
                    # print(f"账户余额: {balance}")
                    return balance
                else:
                    # print("余额识别失败：未识别到数字")
                    return None
            else:
                # print("余额识别失败：OCR无结果")
                return None
                
        except Exception as e:
            print(f"余额识别出错: {e}")
            return None

if __name__ == "__main__":
    delta = DeltaForceClass()
    print(delta.get_balance())
