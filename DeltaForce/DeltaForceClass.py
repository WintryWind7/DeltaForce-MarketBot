from DeltaForceRecognize import DeltaForceRecognize
import pyautogui
import time
import numpy as np
from PIL import Image

class DeltaForceClass(DeltaForceRecognize):
    """
    DeltaForce游戏自动化操作类
    
    该类继承自DeltaForceRecognize类，专门用于实现游戏内的各种自动化操作。
    主要功能包括：
    - 游戏窗口的自动定位和管理
    - 游戏界面元素的识别和交互
    - 账户余额的自动识别
    - 其他游戏内单个具体行为的自动化实现
    
    该类将识别功能与实际操作功能结合，提供完整的游戏自动化解决方案。
    所有的操作都基于屏幕坐标比例，确保在不同分辨率下的兼容性。
    
    Attributes:
        继承自DeltaForceRecognize的所有属性，包括：
        - ocr: OCR识别器实例
        - window_info: 游戏窗口信息
        - 其他识别相关的配置参数
    
    Methods:
        get_balance(): 识别并获取游戏内账户余额
        get_bar_price(): 识别价格条区域的数字
        get_sell_price(): 识别出售价格区域的数字
        click_ratio(x_ratio, y_ratio, do_after, do_wait): 根据比例坐标进行点击的封装方法
        goto(action): 通用位置点击方法，支持多种预定义操作
        其他自动化操作方法将在此基础上扩展
    """
    
    def __init__(self):
        """
        初始化DeltaForce自动化操作类
        
        执行以下初始化步骤：
        1. 调用父类DeltaForceRecognize的初始化方法，设置OCR识别器
        2. 导入并配置pyautogui库，用于自动化鼠标和键盘操作
        3. 自动查找并绑定DeltaForce游戏进程窗口
        
        初始化完成后，类实例将具备完整的游戏识别和操作能力。
        """
        super().__init__()
        # 导入pyautogui并借用其DPI感知功能，确保在高DPI显示器上正确工作
        import pyautogui
        # 自动查找DeltaForce游戏进程并获取窗口信息
        self.find_deltaforce_process()
        # 自动切换到游戏窗口
        self.switch_to_deltaforce_window()
    
    def get_balance(self, m3_ratio=(0.8066, 0.0866), m4_ratio=(0.7555, 0.2777), m5_ratio=(0.8566, 0.2914)):
        """
        自动识别游戏内账户余额
        
        该方法通过以下步骤自动获取账户余额：
        1. 点击指定位置触发余额显示界面
        2. 截取包含余额信息的屏幕区域
        3. 使用OCR技术识别数字内容
        4. 解析并返回余额数值
        
        所有坐标使用相对于游戏窗口的比例坐标，确保在不同分辨率下的兼容性。
        
        Args:固定值
            m3_ratio (tuple): 触发余额显示的点击位置比例坐标 (x_ratio, y_ratio)
                            默认值 (0.8066, 0.0866) 对应游戏界面中的余额按钮位置
            m4_ratio (tuple): 余额显示区域左上角的比例坐标 (x_ratio, y_ratio)
                            默认值 (0.7555, 0.2777) 定义截图区域的起始点
            m5_ratio (tuple): 余额显示区域右下角的比例坐标 (x_ratio, y_ratio)
                            默认值 (0.8566, 0.2914) 定义截图区域的结束点
            
        Returns:
            int: 成功识别时返回账户余额数值
            None: 识别失败时返回None，可能的失败原因包括：
                 - 游戏界面未正确显示
                 - OCR识别失败
                 - 截图区域无有效数字内容
                 
        Raises:
            Exception: 当操作过程中发生错误时，会捕获异常并打印错误信息
            
        Example:
            >>> delta = DeltaForceClass()
            >>> balance = delta.get_balance()
            >>> if balance is not None:
            ...     print(f"当前余额: {balance}")
            ... else:
            ...     print("余额识别失败")
        """
        try:
            # 步骤1: 点击余额按钮位置，触发余额显示界面
            time.sleep(0.2)  # 预等待，确保界面稳定
            m3_screen = self.ratio_to_screen_coords(m3_ratio[0], m3_ratio[1])
            pyautogui.moveTo(m3_screen[0], m3_screen[1])
            pyautogui.click(m3_screen[0], m3_screen[1])
            time.sleep(0.3)  # 等待游戏界面响应，确保余额信息完全加载
            
            # 步骤2: 将比例坐标转换为屏幕绝对坐标
            m4_screen = self.ratio_to_screen_coords(m4_ratio[0], m4_ratio[1])  # 截图区域左上角
            m5_screen = self.ratio_to_screen_coords(m5_ratio[0], m5_ratio[1])  # 截图区域右下角
            
            # 步骤3: 计算截图区域的边界坐标
            # 确保left < right 和 top < bottom，处理可能的坐标顺序问题
            left = min(m4_screen[0], m5_screen[0])
            top = min(m4_screen[1], m5_screen[1])
            right = max(m4_screen[0], m5_screen[0])
            bottom = max(m4_screen[1], m5_screen[1])
            
            # 步骤4: 截取包含余额信息的屏幕区域
            screenshot = pyautogui.screenshot(region=(left, top, right-left, bottom-top))
            screenshot_array = np.array(screenshot)  # 转换为numpy数组供OCR使用
            
            # 步骤5: 使用OCR技术识别截图中的数字内容
            # 配置OCR参数以优化数字识别准确性
            results = self.ocr.reader.readtext(
                screenshot_array,
                allowlist='1234567890',  # 限制只识别数字字符，提高准确性
                width_ths=0.7,          # 文本框宽度阈值
                height_ths=0.7,         # 文本框高度阈值
                text_threshold=0.5,     # 文本置信度阈值
                decoder='beamsearch'    # 使用束搜索解码器提高识别准确性
            )
            
            # 步骤6: 处理OCR识别结果并提取余额数值
            if results:
                # 合并所有识别到的数字文本片段
                combined_text = ""
                for (bbox, text, confidence) in results:
                    # 过滤非数字字符，只保留数字
                    filtered_text = ''.join(char for char in text if char.isdigit())
                    combined_text += filtered_text
                
                # 将合并后的数字字符串转换为整数
                if combined_text:
                    balance = int(combined_text)
                    # print(f"成功识别账户余额: {balance}")  # 调试用输出
                    return balance
                else:
                    # print("余额识别失败：OCR结果中未找到有效数字")
                    return None
            else:
                # print("余额识别失败：OCR未返回任何识别结果")
                return None
                
        except Exception as e:
            # 捕获并处理所有可能的异常情况
            print(f"余额识别过程中发生错误: {e}")
            return None

    def get_bar_price(self):
        """
        识别价格条区域的数字
        
        该方法识别屏幕上指定区域(2305.6938到2862.7101)的数字内容。
        使用OCR技术只识别数字字符，适用于价格、数量等数值的识别。
        
        Returns:
            str: 成功识别时返回数字字符串
            None: 识别失败时返回None，可能的失败原因包括：
                 - 指定区域无有效数字内容
                 - OCR识别失败
                 - 截图操作失败
                 
        Example:
            >>> delta = DeltaForceClass()
            >>> price = delta.get_bar_price()
            >>> if price is not None:
            ...     print(f"识别到的价格: {price}")
            ... else:
            ...     print("价格识别失败")
        """
        try:
            # 定义识别区域的比例坐标
            top_left_ratio = (0.2305, 0.6938)      # 左上角坐标
            bottom_right_ratio = (0.2862, 0.7101)  # 右下角坐标
            
            # 将比例坐标转换为屏幕坐标
            screen_left, screen_top = self.ratio_to_screen_coords(top_left_ratio[0], top_left_ratio[1])
            screen_right, screen_bottom = self.ratio_to_screen_coords(bottom_right_ratio[0], bottom_right_ratio[1])
            
            # 截图指定区域
            screenshot = pyautogui.screenshot(region=(screen_left, screen_top, screen_right-screen_left, screen_bottom-screen_top))
            screenshot_array = np.array(screenshot)
            
            # 使用OCR识别，只识别数字
            results = self.ocr.reader.readtext(
                screenshot_array,
                allowlist='1234567890',  # 限制只识别数字字符
                width_ths=0.7,
                height_ths=0.7,
                text_threshold=0.5,
                decoder='beamsearch'
            )
            
            # 处理识别结果
            if results:
                # 合并所有识别到的数字
                combined_text = ""
                for (bbox, text, confidence) in results:
                    # 只保留数字字符
                    filtered_text = ''.join(char for char in text if char.isdigit())
                    combined_text += filtered_text
                
                if combined_text:
                    print(f"成功识别价格条数字: {combined_text}")
                    return combined_text
                else:
                    # print("价格条识别失败：未识别到有效数字")
                    return None
            else:
                # print("价格条识别失败：OCR无结果")
                return None
                
        except Exception as e:
            print(f"价格条识别过程中发生错误: {e}")
            return None

    def get_sell_price(self):
        """
        识别出售价格区域的数字
        
        该方法识别屏幕上指定区域(6366.5935到7237.6156)的数字内容。
        使用OCR技术只识别数字字符，适用于出售价格等数值的识别。
        
        Returns:
            str: 成功识别时返回数字字符串
            None: 识别失败时返回None，可能的失败原因包括：
                 - 指定区域无有效数字内容
                 - OCR识别失败
                 - 截图操作失败
                 
        Example:
            >>> delta = DeltaForceClass()
            >>> sell_price = delta.get_sell_price()
            >>> if sell_price is not None:
            ...     print(f"识别到的出售价格: {sell_price}")
            ... else:
            ...     print("出售价格识别失败")
        """
        try:
            # 定义识别区域的比例坐标
            top_left_ratio = (0.6366, 0.5935)      # 左上角坐标
            bottom_right_ratio = (0.7237, 0.6156)  # 右下角坐标
            
            # 将比例坐标转换为屏幕坐标
            screen_left, screen_top = self.ratio_to_screen_coords(top_left_ratio[0], top_left_ratio[1])
            screen_right, screen_bottom = self.ratio_to_screen_coords(bottom_right_ratio[0], bottom_right_ratio[1])
            
            # 截图指定区域
            screenshot = pyautogui.screenshot(region=(screen_left, screen_top, screen_right-screen_left, screen_bottom-screen_top))
            screenshot_array = np.array(screenshot)
            
            # 使用OCR识别，只识别数字
            results = self.ocr.reader.readtext(
                screenshot_array,
                allowlist='1234567890',  # 限制只识别数字字符
                width_ths=0.7,
                height_ths=0.7,
                text_threshold=0.5,
                decoder='beamsearch'
            )
            
            # 处理识别结果
            if results:
                # 合并所有识别到的数字
                combined_text = ""
                for (bbox, text, confidence) in results:
                    # 只保留数字字符
                    filtered_text = ''.join(char for char in text if char.isdigit())
                    combined_text += filtered_text
                
                if combined_text:
                    print(f"成功识别出售价格: {combined_text}")
                    return combined_text
                else:
                    # print("出售价格识别失败：未识别到有效数字")
                    return None
            else:
                # print("出售价格识别失败：OCR无结果")
                return None
                
        except Exception as e:
            print(f"出售价格识别过程中发生错误: {e}")
            return None

    def click_ratio(self, x_ratio, y_ratio, do_after=0.0, do_wait=0.0):
        """
        根据比例坐标进行点击的封装方法
        
        该方法提供了一个统一的接口来处理基于比例坐标的点击操作。
        自动将比例坐标转换为屏幕坐标，然后执行点击操作。
        
        Args:
            x_ratio (float): X轴比例坐标，范围0.0-1.0
            y_ratio (float): Y轴比例坐标，范围0.0-1.0
            do_after (float): 点击前等待时间，默认0.0秒（立即点击）
            do_wait (float): 点击后等待时间，默认0.3秒
        
        Returns:
            bool: 点击成功返回True，失败返回False
            
        Example:
            >>> delta = DeltaForceClass()
            >>> # 立即点击屏幕中心位置
            >>> delta.click_ratio(0.5, 0.5)
            >>> # 等待1秒后点击右上角，点击后等待2秒
            >>> delta.click_ratio(0.9, 0.1, do_after=1.0, do_wait=2.0)
        """
        try:
            # 验证坐标范围
            if not (0.0 <= x_ratio <= 1.0 and 0.0 <= y_ratio <= 1.0):
                print(f"坐标超出范围: x_ratio={x_ratio}, y_ratio={y_ratio}")
                return False
            
            # 点击前等待
            if do_after > 0:
                time.sleep(do_after)
            
            # 将比例坐标转换为屏幕坐标
            screen_coords = self.ratio_to_screen_coords(x_ratio, y_ratio)
            
            # 执行点击操作
            pyautogui.moveTo(screen_coords[0], screen_coords[1])
            pyautogui.click(screen_coords[0], screen_coords[1])
            
            # 点击后等待
            if do_wait > 0:
                time.sleep(do_wait)
            
            print(f"成功点击比例坐标 ({x_ratio}, {y_ratio}) -> 屏幕坐标 {screen_coords}")
            return True
            
        except Exception as e:
            print(f"点击操作失败: {e}")
            return False

    def goto(self, action):
        """
        通用位置点击方法，根据action参数执行相应的点击操作
        
        Args:
            action (str): 指定要执行的操作类型
        
        Returns:
            bool: 操作成功返回True，失败返回False
        """
        # 根据action参数执行相应操作
        if action == "555":
            # 点击余额按钮
            return self.click_ratio(0.8066, 0.0866)
             
        elif action == "开始游戏":
            # 点击开始游戏按钮
            return self.click_ratio(0.1057, 0.0866)
            
        elif action == "交易行":
            # 点击交易行按钮
            return self.click_ratio(0.3727, 0.0866)
            
        elif action == "仓库":
            # 点击仓库按钮
            return self.click_ratio(0.1718, 0.0866)
            
        elif action == "出售":
            # 出售操作：先点击交易行，延迟1秒后点击出售位置
            # 第一步：点击交易行
            if not self.click_ratio(0.3727, 0.0866):
                return False
            # 第二步：延迟1秒后点击出售位置
            return self.click_ratio(0.1760, 0.1362, do_after=1.0)
            
        else:
            # 不支持的操作类型
            print(f"不支持的操作类型: {action}")
            return False

# 模块测试代码
if __name__ == "__main__":
    # 创建DeltaForceClass实例
    delta = DeltaForceClass()
    
    # 测试余额识别功能
    # print("=== 测试余额识别功能 ===")
    # balance = delta.get_balance()
    # if balance is not None:
    #     print(f"测试成功 - 当前账户余额: {balance}")
    # else:
    #     print("测试失败 - 无法识别账户余额")
    
    print("\n=== 测试get_bar_price方法功能 ===")
    
    print("测试价格条数字识别:")
    bar_price = delta.get_bar_price()
    if bar_price is not None:
        print(f"✓ 价格条识别成功: {bar_price}")
    else:
        print("✗ 价格条识别失败")
    
    # 测试get_sell_price方法功能
    print("\n=== 测试get_sell_price方法功能 ===")
    
    print("测试出售价格数字识别:")
    sell_price = delta.get_sell_price()
    if sell_price is not None:
        print(f"✓ 出售价格识别成功: {sell_price}")
    else:
        print("✗ 出售价格识别失败")
    
    print("\n=== 测试完成 ===")
    
